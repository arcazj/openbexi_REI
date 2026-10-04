"""Bounded, cached clients for official public scientific APIs.

Coordinates from Ensembl are one-based, closed; zero-based half-open values
are provided separately. GWAS locations are never silently combined with them.
"""

import asyncio
import copy
import re
import time
from collections import OrderedDict
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx
from defusedxml import ElementTree as ET

BASE_URLS = {
    "pubmed": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
    "ensembl": "https://rest.ensembl.org/",
    "gwas": "https://www.ebi.ac.uk/gwas/rest/api/v2/",
}
SOURCE_INFO = [
    {"id": "pubmed", "name": "PubMed", "purpose": "Publications and available abstracts", "browser": False},
    {"id": "ensembl", "name": "Ensembl", "purpose": "Human genes, transcripts, and GRCh38 regions", "browser": True},
    {"id": "gwas", "name": "GWAS Catalog", "purpose": "Curated genetic associations and trait mappings", "browser": False},
]
MAX_REGION = 5_000_000
REQUEST_AUDIT: ContextVar = ContextVar("source_request_audit", default=None)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_region(query: str) -> Dict[str, Any]:
    value = query.strip()
    if re.search(r"GRCh(?!38\b)\d+", value, re.I):
        raise ValueError("Use a GRCh38 region; other assemblies cannot be combined here.")
    value = re.sub(r"\s*(?:\(?GRCh38\)?|\(?hg38\)?)\s*", "", value, flags=re.I)
    match = re.fullmatch(r"(?:chr)?(\d{1,2}|X|Y|MT|M):([\d,]+)(?:-|\.\.)([\d,]+)", value, re.I)
    if not match:
        raise ValueError("Use chr17:43044295-43170245 (GRCh38, one-based inclusive).")
    chromosome = match.group(1).upper().replace("MT", "M")
    if chromosome.isdigit():
        if not 1 <= int(chromosome) <= 22:
            raise ValueError("Select a human chromosome 1-22, X, Y, or MT.")
        chromosome = str(int(chromosome))
    if chromosome == "M":
        chromosome = "MT"
    start, end = (int(match.group(i).replace(",", "")) for i in (2, 3))
    if start < 1 or end < start or end > 250_000_000:
        raise ValueError("Coordinates must be positive, ordered, and within the human genome.")
    if end - start + 1 > MAX_REGION:
        raise ValueError("A region may contain at most 5 million bases.")
    return {"chromosome": chromosome, "start": start, "end": end,
            "start0": start - 1, "end0": end, "assembly": "GRCh38",
            "coordinate_convention": "1-based inclusive"}


def interpret(query: str, mode: str = "auto") -> Dict[str, Any]:
    term = " ".join(query.strip().split())
    if not term or len(term) > 250 or any(ord(ch) < 32 for ch in query):
        raise ValueError("Enter a research topic, gene, or region of 1-250 characters.")
    kind = mode
    if mode == "auto":
        if re.match(r"(?:chr)?(?:\d{1,2}|X|Y|MT|M):", term, re.I):
            kind = "region"
        elif term.upper() in {"PCOS", "POI", "IVF", "ICSI", "REI", "ART", "RPL"}:
            kind = "topic"
        elif re.fullmatch(r"ENS[GPT]\d+(?:\.\d+)?", term, re.I) or re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*\d+", term) or re.fullmatch(r"[A-Z][A-Z0-9-]{1,15}", term):
            kind = "gene"
        else:
            kind = "topic"
    result = {"type": kind, "term": term, "organism": "Homo sapiens", "assembly": "GRCh38"}
    if kind == "region":
        result["region"] = parse_region(term)
        result["term"] = "{chromosome}:{start}-{end}".format(**result["region"])
    if kind == "gene":
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,40}", term):
            raise ValueError("Enter one gene symbol or Ensembl identifier.")
        result["term"] = term.upper()
    return result


def node_text(node: Any) -> str:
    return "" if node is None else "".join(node.itertext()).strip()


def pubmed_records(xml_bytes: bytes) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    records = []
    for item in root.findall(".//PubmedArticle"):
        citation = item.find("MedlineCitation")
        if citation is None:
            continue
        pmid = node_text(citation.find("PMID"))
        article = citation.find("Article")
        if article is None or not pmid.isdigit():
            continue
        title = node_text(article.find("ArticleTitle"))
        sections = []
        for section in article.findall("Abstract/AbstractText"):
            text = node_text(section)
            label = section.get("Label")
            sections.append((label + ": " if label else "") + text)
        abstract = "\n\n".join(sections)
        types = [node_text(n) for n in article.findall("PublicationTypeList/PublicationType")]
        mesh = [node_text(n) for n in citation.findall("MeshHeadingList/MeshHeading/DescriptorName")]
        species = "Human" if "Humans" in mesh else "Animal" if "Animals" in mesh else "Not specified in indexed metadata"
        if "Humans" in mesh and "Animals" in mesh:
            species = "Human and animal"
        authors = []
        for author in article.findall("AuthorList/Author")[:12]:
            name = node_text(author.find("CollectiveName")) or " ".join(filter(None, [node_text(author.find("LastName")), node_text(author.find("Initials"))]))
            if name:
                authors.append(name)
        year = node_text(article.find("Journal/JournalIssue/PubDate/Year"))
        if not year:
            match = re.search(r"\d{4}", node_text(article.find("Journal/JournalIssue/PubDate/MedlineDate")))
            year = match.group() if match else None
        notices = []
        for notice in citation.findall("CommentsCorrectionsList/CommentsCorrections"):
            ref_type = notice.get("RefType", "")
            if ref_type in {"RetractionIn", "RetractionOf", "ErratumIn", "ErratumFor", "ExpressionOfConcernIn", "ExpressionOfConcernFor", "UpdateIn", "UpdateOf"}:
                linked_id = node_text(notice.find("PMID"))
                notices.append({"type": ref_type, "pmid": linked_id,
                                "url": "https://pubmed.ncbi.nlm.nih.gov/" + linked_id + "/" if linked_id.isdigit() else None,
                                "reference": node_text(notice.find("RefSource"))})
        metadata = {"pmid": pmid, "journal": node_text(article.find("Journal/Title")),
                    "publication_types": types, "study_design": ", ".join(types) or "Not indexed",
                    "species": species, "population": "Not extracted; inspect the abstract or full text",
                    "sample_size": "Not extracted", "abstract_available": bool(abstract),
                    "evidence_scope": "Abstract and bibliographic metadata" if abstract else "Bibliographic metadata only",
                    "notices": notices, "retracted": "Retracted Publication" in types or any(n["type"] == "RetractionIn" for n in notices),
                    "source_version": "NCBI E-utilities", "retrieved_at": utc_now()}
        records.append({"id": "pubmed:" + pmid, "source": "pubmed", "type": "publication", "title": title,
                        "summary": abstract[:8000] or "No abstract is available. Open the source record for details.",
                        "url": "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/", "year": year,
                        "authors": authors, "metadata": metadata})
    return records


def ensembl_record(data: Dict[str, Any]) -> Dict[str, Any]:
    assembly = data.get("assembly_name")
    if assembly != "GRCh38":
        raise ValueError("Ensembl returned an incompatible or unspecified assembly; expected GRCh38.")
    identifier = str(data.get("id", ""))
    if not re.fullmatch(r"ENS[GPT]\d+", identifier):
        raise ValueError("Ensembl returned an unsupported identifier.")
    start, end = int(data["start"]), int(data["end"])
    transcripts = [{"id": t.get("id"), "name": t.get("display_name"), "start": t.get("start"), "end": t.get("end"),
                    "biotype": t.get("biotype"), "is_canonical": t.get("is_canonical", 0)}
                   for t in data.get("Transcript", [])[:100]]
    metadata = {"ensembl_id": identifier, "chromosome": str(data["seq_region_name"]),
                "start": start, "end": end, "start0": start - 1, "end0": end, "strand": data.get("strand"),
                "assembly": assembly, "coordinate_convention": "1-based inclusive",
                "normalized_coordinate_convention": "0-based half-open", "organism": "Homo sapiens",
                "biotype": data.get("biotype"), "object_type": data.get("object_type", "Gene"),
                "transcripts": transcripts, "transcripts_truncated": len(data.get("Transcript", [])) > 100,
                "source_version": "Ensembl REST; record version " + str(data.get("version", "unavailable")), "retrieved_at": utc_now()}
    return {"id": "ensembl:" + identifier, "source": "ensembl", "type": "gene",
            "title": data.get("display_name") or identifier, "summary": data.get("description") or "Genomic feature annotation",
            "url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=" + identifier, "metadata": metadata}


def collection(data: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    return data.get("_embedded", {}).get(key, data.get(key, data.get("content", []))) or []


def gwas_record(data: Dict[str, Any]) -> Dict[str, Any]:
    identifier = str(data.get("association_id", data.get("id", "")))
    traits = data.get("reported_trait") or [t.get("efo_trait", "") for t in data.get("efo_traits", [])]
    if isinstance(traits, str):
        traits = [traits]
    alleles = data.get("snp_effect_allele") or [a.get("rs_id", "") for a in data.get("snp_allele", [])]
    if isinstance(alleles, str):
        alleles = [alleles]
    pvalue = data.get("p_value")
    title = ", ".join(traits) or "Reported GWAS association"
    metadata = {"association_id": identifier, "traits": data.get("efo_traits", []), "reported_traits": traits,
                "variants": alleles, "mapped_genes": data.get("mapped_genes", []), "locations": data.get("locations", []),
                "p_value": pvalue, "beta": data.get("beta"), "risk_frequency": data.get("risk_frequency"),
                "study_accession": data.get("accession_id"), "pmid": str(data.get("pubmed_id", "")),
                "assembly": "Not supplied in association response; verify study/source before genomic comparison",
                "coordinate_convention": "Not supplied; locations are not normalized or combined",
                "population": "Not supplied in association response; inspect the study",
                "sample_size": "Not supplied in association response", "study_design": "Genome-wide association study",
                "source_version": "GWAS Catalog REST API v2", "retrieved_at": utc_now(),
                "association_caution": "Association does not establish causation or a causal gene."}
    return {"id": "gwas:" + identifier, "source": "gwas", "type": "association", "title": title,
            "summary": ", ".join(alleles) + ("; P=" + str(pvalue) if pvalue is not None else "") + ". Reported association; causality is not established.",
            "url": "https://www.ebi.ac.uk/gwas/studies/" + str(data.get("accession_id", "")),
            "authors": [data["first_author"]] if data.get("first_author") else [], "metadata": metadata}


class SourceService:
    def __init__(self, client: httpx.AsyncClient, ncbi_email: str = ""):
        self.client = client
        self.ncbi_email = ncbi_email
        self.cache: OrderedDict = OrderedDict()
        self.locks = {source: asyncio.Lock() for source in BASE_URLS}
        self.last_request = {source: 0.0 for source in BASE_URLS}

    async def request(self, source: str, path: str, params: Dict[str, Any], xml: bool = False) -> Any:
        if source not in BASE_URLS or path.startswith(("/", "http")) or ".." in path:
            raise ValueError("Only configured scientific API endpoints are allowed.")
        cache_key = (source, path, tuple(sorted((k, str(v)) for k, v in params.items())), xml)
        cached = self.cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < 300:
            self.cache.move_to_end(cache_key)
            if REQUEST_AUDIT.get() is not None:
                REQUEST_AUDIT.get().append({"endpoint": BASE_URLS[source] + path, "parameters": dict(params), "cached": True, "fetched_at": cached[2]})
            return copy.deepcopy(cached[1])
        delay = {"pubmed": 0.36, "ensembl": 0.08, "gwas": 0.65}[source]
        for attempt in range(3):
            async with self.locks[source]:
                wait = delay - (time.monotonic() - self.last_request[source])
                if wait > 0:
                    await asyncio.sleep(wait)
                self.last_request[source] = time.monotonic()
                response = await self.client.get(BASE_URLS[source] + path, params=params,
                                                 headers={"Accept": "application/xml" if xml else "application/json"})
            if response.status_code in (429, 502, 503, 504) and attempt < 2:
                try:
                    wait = min(4.0, max(0.3, float(response.headers.get("Retry-After", 0.4 * (2 ** attempt)))))
                except ValueError:
                    wait = 0.4 * (2 ** attempt)
                await asyncio.sleep(wait)
                continue
            response.raise_for_status()
            if len(response.content) > 3_000_000:
                raise ValueError("The source response is too large; narrow the search.")
            result = response.content if xml else response.json()
            fetched_at = utc_now()
            self.cache[cache_key] = (time.monotonic(), copy.deepcopy(result), fetched_at)
            if REQUEST_AUDIT.get() is not None:
                REQUEST_AUDIT.get().append({"endpoint": BASE_URLS[source] + path, "parameters": dict(params), "cached": False, "fetched_at": fetched_at})
            self.cache.move_to_end(cache_key)
            while len(self.cache) > 128:
                self.cache.popitem(last=False)
            return result
        raise ValueError("Source temporarily unavailable.")

    async def pubmed(self, interpretation: Dict[str, Any], limit: int) -> Dict[str, Any]:
        query = interpretation["term"]
        params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": limit, "sort": "relevance", "tool": "REIResearchExplorer"}
        if self.ncbi_email:
            params["email"] = self.ncbi_email
        result = await self.request("pubmed", "esearch.fcgi", params)
        search = result.get("esearchresult", {})
        if "errorlist" in search or "ERROR" in result:
            raise ValueError("PubMed could not interpret this query; simplify its terms.")
        ids = [i for i in search.get("idlist", []) if str(i).isdigit()][:limit]
        records = []
        if ids:
            fetch_params = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml", "tool": "REIResearchExplorer"}
            if self.ncbi_email:
                fetch_params["email"] = self.ncbi_email
            records = pubmed_records(await self.request("pubmed", "efetch.fcgi", fetch_params, xml=True))
        return {"records": records, "total": int(search.get("count", 0)),
                "query": search.get("querytranslation", query), "query_parameters": params,
                "truncated": int(search.get("count", 0)) > len(records)}

    async def ensembl(self, interpretation: Dict[str, Any], limit: int) -> Dict[str, Any]:
        term = interpretation["term"]
        if interpretation["type"] == "region":
            data = await self.request("ensembl", "overlap/region/homo_sapiens/" + quote(term, safe=":"),
                                      {"feature": "gene", "content-type": "application/json"})
            records = [ensembl_record(item) for item in data[:limit]]
            return {"records": records, "total": len(data), "query": "GRCh38 region " + term + "; feature=gene",
                    "truncated": len(data) > len(records)}
        if re.fullmatch(r"ENS[GPT]\d+(?:\.\d+)?", term):
            path = "lookup/id/" + term.split(".")[0]
        else:
            path = "lookup/symbol/homo_sapiens/" + quote(term, safe="")
        try:
            data = await self.request("ensembl", path, {"expand": 1, "content-type": "application/json"})
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (400, 404):
                return {"records": [], "total": 0, "query": term, "truncated": False}
            raise
        return {"records": [ensembl_record(data)], "total": 1, "query": term + "; expand=1", "truncated": False}

    async def gwas(self, interpretation: Dict[str, Any], limit: int) -> Dict[str, Any]:
        term = interpretation["term"]
        params = {"page": 0, "size": limit, "extended_geneset": "false"}
        if re.fullmatch(r"rs\d+", term, re.I):
            params["rs_id"] = term.lower()
        elif interpretation["type"] == "gene":
            params["mapped_gene"] = term
        else:
            traits = await self.request("gwas", "efo-traits", {"efo_trait": term, "page": 0, "size": 5})
            matches = collection(traits, "efo_traits")
            if not matches:
                return {"records": [], "total": 0, "query": "Trait names containing: " + term,
                        "truncated": False, "note": "No matching indexed traits. This does not establish absence of research."}
            # Use the exact name when found; otherwise search up to three explicitly reported mappings.
            exact = [t for t in matches if t.get("efo_trait", "").lower() == term.lower()]
            chosen = exact[:1] or matches[:3]
            records_by_id: Dict[str, Any] = {}
            total = 0
            queried = []
            for trait in chosen:
                trait_params = dict(params, efo_id=trait["efo_id"], show_child_trait="false")
                data = await self.request("gwas", "associations", trait_params)
                queried.append(trait["efo_id"] + " (" + trait.get("efo_trait", "") + ")")
                total += int(data.get("page", {}).get("totalElements", len(collection(data, "associations"))))
                for item in collection(data, "associations"):
                    record = gwas_record(item)
                    records_by_id[record["id"]] = record
            records = list(records_by_id.values())[:limit]
            mapping_limited = len(matches) > len(chosen) and not exact
            return {"records": records, "total": total, "total_is_upper_bound": len(chosen) > 1,
                    "query": "Trait search: " + term + "; associations for " + "; ".join(queried) + "; child traits excluded",
                    "query_parameters": {"trait_search": term, "efo_ids": [t["efo_id"] for t in chosen], "page": 0, "size": limit, "show_child_trait": False},
                    "truncated": total > len(records) or mapping_limited,
                    "note": "At most 3 of the first 5 matched traits were searched; counts across traits may overlap." if len(chosen) > 1 or mapping_limited else "Exact matched trait; child traits excluded."}
        data = await self.request("gwas", "associations", params)
        records = [gwas_record(item) for item in collection(data, "associations")[:limit]]
        total = int(data.get("page", {}).get("totalElements", len(records)))
        return {"records": records, "total": total, "query": "; ".join(k + "=" + str(v) for k, v in params.items()),
                "query_parameters": params, "truncated": total > len(records)}

    async def search(self, source: str, interpretation: Dict[str, Any], limit: int) -> Dict[str, Any]:
        retrieved_at = utc_now()
        coverage = {"source": source, "status": "ok", "total": 0, "retrieved": 0, "truncated": False,
                    "query": interpretation["term"], "retrieved_at": retrieved_at}
        audit: List[Dict[str, Any]] = []
        audit_token = REQUEST_AUDIT.set(audit)
        if (source == "ensembl" and interpretation["type"] == "topic") or (source in {"pubmed", "gwas"} and interpretation["type"] == "region"):
            coverage.update(status="skipped", note="Use a gene or region for Ensembl." if source == "ensembl" else "Region searches use Ensembl; topic or gene queries can search this source.")
            REQUEST_AUDIT.reset(audit_token)
            return {"records": [], "coverage": coverage}
        try:
            result = await asyncio.wait_for(getattr(self, source)(interpretation, limit), timeout=35)
            records = result.pop("records")
            coverage.update(result, retrieved=len(records))
            return {"records": records, "coverage": coverage}
        except (httpx.TimeoutException, asyncio.TimeoutError):
            message = "The source timed out. Retry or search fewer sources."
        except httpx.HTTPStatusError as exc:
            message = "The source is rate limiting requests. Retry shortly." if exc.response.status_code == 429 else "The source returned HTTP " + str(exc.response.status_code) + ". Retry shortly."
        except httpx.RequestError:
            message = "Cannot reach the source. Check your internet connection and retry."
        except (ValueError, KeyError, TypeError) as exc:
            message = str(exc) if isinstance(exc, ValueError) else "The source returned an unexpected record format."
        except Exception:
            message = "This source could not be processed. Retry or use another source."
        finally:
            coverage["requests"] = audit
            coverage["cached"] = bool(audit) and all(entry["cached"] for entry in audit)
            REQUEST_AUDIT.reset(audit_token)
        coverage.update(status="error", error=message[:250], total=None)
        return {"records": [], "coverage": coverage}
