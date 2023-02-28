from seleniumbase import BaseCase

from tests.end2end.end2end_test_setup import End2EndTestSetup
from tests.end2end.server import SDocTestServer


class Test_UC03_T02_CreateBeforeSection(BaseCase):
    def test_01(self):
        test_setup = End2EndTestSetup(path_to_test_file=__file__)

        with SDocTestServer(
            input_path=test_setup.path_to_sandbox
        ) as test_server:
            self.open(test_server.get_host_and_port())

            self.assert_text("Document 1")
            self.assert_text("PROJECT INDEX")

            self.click_xpath('//*[@data-testid="tree-file-link"]')
            self.assert_text("Hello world!")

            self.hover_and_click(
                "sdoc-node", '[data-testid="node-menu-handler"]'
            )
            self.click('[data-testid="node-add-section-above-action"]')

            self.type("#section_title", "Section A")
            self.type("#section_content", "Section A text.")

            self.click_xpath('//*[@data-testid="form-submit-action"]')

            self.assert_text("1. Section A")
            self.assert_text("2. Section B")

            self.assert_element(
                "//turbo-frame[@id='frame-toc']//*[contains(., 'Section A')]"
            )
            self.assert_element(
                "//turbo-frame[@id='frame-toc']//*[contains(., 'Section B')]"
            )

        assert test_setup.compare_sandbox_and_expected_output()