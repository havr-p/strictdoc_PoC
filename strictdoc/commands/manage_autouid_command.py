import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from strictdoc.backend.sdoc.errors.document_tree_error import DocumentTreeError
from strictdoc.backend.sdoc.models.document import Document
from strictdoc.backend.sdoc.models.requirement import Requirement
from strictdoc.backend.sdoc.writer import SDWriter
from strictdoc.core.document_iterator import DocumentCachingIterator
from strictdoc.core.project_config import ProjectConfig
from strictdoc.core.traceability_index import TraceabilityIndex
from strictdoc.core.traceability_index_builder import TraceabilityIndexBuilder
from strictdoc.helpers.parallelizer import Parallelizer


def extract_last_numeric_part(string: str) -> str:
    regex_match = re.match(".*?([0-9]+)$", string)
    if regex_match is not None:
        return regex_match.group(1)
    raise ValueError(f"Cannot extract the numeric part of UID: {string}")


@dataclass
class PrefixDataAccumulator:
    existing_requirements_uid_numbers: List[int] = field(default_factory=list)
    requirements_without_uid: List[Requirement] = field(default_factory=list)


class ManageAutoUIDCommand:
    @staticmethod
    def execute(*, project_config: ProjectConfig, parallelizer: Parallelizer):
        try:
            traceability_index: TraceabilityIndex = (
                TraceabilityIndexBuilder.create(
                    project_config=project_config,
                    parallelizer=parallelizer,
                )
            )
        except DocumentTreeError as exc:
            print(exc.to_print_message())  # noqa: T201
            sys.exit(1)

        accumulators: Dict[str, PrefixDataAccumulator] = defaultdict(
            PrefixDataAccumulator
        )
        for document in traceability_index.document_tree.document_list:
            ManageAutoUIDCommand._process_document(document, accumulators)

        for prefix, accumulator in accumulators.items():
            next_number = (
                max(accumulator.existing_requirements_uid_numbers) + 1
                if len(accumulator.existing_requirements_uid_numbers) > 0
                else 1
            )
            for requirement in accumulator.requirements_without_uid:
                requirement_uid = f"{prefix}{next_number}"
                requirement.set_field_value(
                    field_name="UID", form_field_index=0, value=requirement_uid
                )
                next_number += 1

        for document in traceability_index.document_tree.document_list:
            document_content = SDWriter().write(document)
            document_meta = document.meta
            with open(
                document_meta.input_doc_full_path, "w", encoding="utf8"
            ) as output_file:
                output_file.write(document_content)

    @staticmethod
    def _process_document(
        document: Document, accumulators: Dict[str, PrefixDataAccumulator]
    ):
        document_iterator = DocumentCachingIterator(document)

        for node in document_iterator.all_content():
            if not isinstance(node, Requirement):
                continue
            requirement: Requirement = node

            requirement_prefix: str = requirement.get_requirement_prefix()
            current_accumulator = accumulators[requirement_prefix]

            if requirement.reserved_uid is not None:
                if not requirement.reserved_uid.startswith(requirement_prefix):
                    print(  # noqa: T201
                        "warning: "
                        "Skipping a requirement because its UID does not match "
                        f"the applicable requirement prefix "
                        f"'{requirement_prefix}': "
                        f"'{requirement.reserved_uid}'."
                    )
                    continue
                try:
                    requirement_uid_numeric_part = extract_last_numeric_part(
                        requirement.reserved_uid
                    )
                except ValueError:
                    print(  # noqa: T201
                        "Not clear how to deal with an unusual identifier, "
                        "skipping it: "
                        f"{requirement.reserved_uid}."
                    )
                    continue
                if len(requirement_uid_numeric_part) == 0:
                    continue
                requirement_uid_number = int(requirement_uid_numeric_part)
                current_accumulator.existing_requirements_uid_numbers.append(
                    requirement_uid_number
                )
            else:
                current_accumulator.requirements_without_uid.append(requirement)
