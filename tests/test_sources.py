"""Scientific input and source coverage tests; public HTTP is always mocked."""

import unittest
from unittest.mock import AsyncMock, patch

import httpx

from backend.sources import SourceService, ensembl_record, interpret, parse_region, pubmed_records


PUBMED_XML = b'''<PubmedArticleSet><PubmedArticle><MedlineCitation>
<PMID>123456</PMID><Article><ArticleTitle>Fixture human cohort</ArticleTitle>
<Journal><Title>Fixture journal</Title><JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue></Journal>
<Abstract><AbstractText Label="METHODS">An observational cohort was studied.</AbstractText></Abstract>
<PublicationTypeList><PublicationType>Observational Study</PublicationType></PublicationTypeList></Article>
<MeshHeadingList><MeshHeading><DescriptorName>Humans</DescriptorName></MeshHeading></MeshHeadingList>
<CommentsCorrectionsList><CommentsCorrections RefType="RetractionIn"><RefSource>Fixture notice</RefSource><PMID>654321</PMID></CommentsCorrections></CommentsCorrectionsList>
</MedlineCitation></PubmedArticle></PubmedArticleSet>'''


class GenomicCoordinateTests(unittest.TestCase):
    def test_region_retains_one_based_inclusive_endpoints(self):
        region = parse_region("chr17:43044295-43125483")
        self.assertEqual(region["start"], 43044295)
        self.assertEqual(region["end"], 43125483)
        self.assertEqual(region["assembly"], "GRCh38")
        self.assertIn("1-based", region["coordinate_convention"])
        self.assertIn("inclusive", region["coordinate_convention"])
        self.assertEqual(region["start0"], region["start"] - 1)
        self.assertEqual(region["end0"], region["end"])

    def test_single_base_region_is_valid(self):
        region = parse_region("17:43044295-43044295")
        self.assertEqual(region["start"], region["end"])

    def test_invalid_coordinates_cannot_be_sent_to_ensembl(self):
        for query in ("chr17:0-10", "chr17:20-10", "chr17:-1-10", "chr17:1.5-10", "chrZ:1-10"):
            with self.subTest(query=query):
                with self.assertRaises(ValueError):
                    parse_region(query)

    def test_different_assembly_and_excessive_region_are_rejected(self):
        for query in ("chr17:1-10 GRCh37", "chr17:1-5000001"):
            with self.subTest(query=query):
                with self.assertRaises(ValueError):
                    parse_region(query)

    def test_gene_assembly_is_checked_before_coordinates_are_combined(self):
        for assembly in ("GRCh37", None):
            with self.subTest(assembly=assembly):
                with self.assertRaises(ValueError):
                    ensembl_record({"id": "ENSG00000012048", "assembly_name": assembly, "start": 1, "end": 2, "seq_region_name": "17"})


class PublicationEvidenceTests(unittest.TestCase):
    def test_retraction_and_study_context_are_preserved_without_inferred_sample_size(self):
        record = pubmed_records(PUBMED_XML)[0]
        self.assertEqual(record["id"], "pubmed:123456")
        self.assertEqual(record["metadata"]["species"], "Human")
        self.assertEqual(record["metadata"]["study_design"], "Observational Study")
        self.assertTrue(record["metadata"]["retracted"])
        self.assertEqual(record["metadata"]["notices"][0]["url"], "https://pubmed.ncbi.nlm.nih.gov/654321/")
        self.assertEqual(record["metadata"]["sample_size"], "Not extracted")
        self.assertIn("Abstract", record["metadata"]["evidence_scope"])
        self.assertIn("METHODS:", record["summary"])


class SourceCoverageTests(unittest.IsolatedAsyncioTestCase):
    async def search(self, source, handler, mode="topic", query="ovarian aging"):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with patch("backend.sources.asyncio.sleep", new=AsyncMock()):
                return await SourceService(client).search(source, interpret(query, mode), 10)

    async def test_upstream_timeout_is_a_failure_without_fabricated_results(self):
        def handler(request):
            raise httpx.ReadTimeout("fixture timeout", request=request)
        result = await self.search("pubmed", handler)
        self.assertEqual(result["records"], [])
        self.assertEqual(result["coverage"]["status"], "error")
        self.assertIsNone(result["coverage"]["total"])
        self.assertIn("timed out", result["coverage"]["error"])

    async def test_successful_empty_search_is_distinct_from_retrieval_failure(self):
        calls = []
        def handler(request):
            calls.append(request.url.path)
            return httpx.Response(200, json={"esearchresult": {"count": "0", "idlist": []}})
        result = await self.search("pubmed", handler)
        self.assertEqual(result["coverage"]["status"], "ok")
        self.assertEqual(result["coverage"]["total"], 0)
        self.assertFalse(result["coverage"]["truncated"])
        self.assertEqual(result["records"], [])
        self.assertEqual(len(calls), 1)

    async def test_limited_pubmed_search_reports_full_count_and_actual_query(self):
        def handler(request):
            if request.url.path.endswith("esearch.fcgi"):
                return httpx.Response(200, json={"esearchresult": {"count": "27", "idlist": ["123456"], "querytranslation": "ovarian aging[All Fields]"}})
            return httpx.Response(200, content=PUBMED_XML)
        result = await self.search("pubmed", handler)
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["coverage"]["retrieved"], 1)
        self.assertEqual(result["coverage"]["total"], 27)
        self.assertTrue(result["coverage"]["truncated"])
        self.assertEqual(result["coverage"]["query"], "ovarian aging[All Fields]")
        self.assertEqual(result["coverage"]["query_parameters"]["term"], "ovarian aging")

    async def test_incompatible_upstream_assembly_has_no_genomic_results(self):
        def handler(request):
            return httpx.Response(200, json={"id": "ENSG00000012048", "assembly_name": "GRCh37", "start": 1, "end": 2, "seq_region_name": "17"})
        result = await self.search("ensembl", handler, mode="gene", query="BRCA1")
        self.assertEqual(result["records"], [])
        self.assertEqual(result["coverage"]["status"], "error")
        self.assertIn("assembly", result["coverage"]["error"])


if __name__ == "__main__":
    unittest.main()
