from typing import Any, Literal, Type, cast

from django.db.models import Model
from django.forms.models import model_to_dict

from ..bit import Bit
from ..serializers import DatabaseDiffSerializer


class DatabaseDiff(Bit):
    """Compare the state of the database before and after a test."""

    # TODO: Change this to DictSerializer
    serializer_class = DatabaseDiffSerializer

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the DatabaseDiff bit.

        Args:
        ----
        models (list[Type[Model]], default=[]): A list of models to compare.
        *args: Arguments to pass to the Bit superclass.
        **kwargs: Keyword arguments to pass to the Bit superclass.
        """
        models = kwargs.pop("models", None)

        super().__init__(*args, **kwargs)
        self.models = cast(list[Type[Model]], models or getattr(self, "models", []))
        self.record_data: dict[Type[Model], dict[int, dict[str, Any]]] = {}
        self.diffs: dict[Type[Model], dict[str, Any]] = {}

    def __enter__(self) -> "DatabaseDiff":
        """Take a list of models and record their table data."""
        for model in self.models:
            self.record_data[model] = self._generate_record_data(model)

        return self

    def __exit__(self, *args: Any) -> Literal[False]:
        """Compare the state of the database before and after a test."""
        self._generate_diff()
        return False

    @property
    def data(self) -> list[dict[str, Any]]:
        """Return the differences between the database before and after a test."""
        result = []
        for model in self.models:
            result.append(
                {
                    "model": f"{model.__name__}",
                    "added": self.diffs[model]["added"],
                    "removed": self.diffs[model]["removed"],
                    "altered": self.diffs[model]["altered"],
                },
            )
        return result

    def _generate_record_data(self, model: Type[Model]) -> dict[int, dict[str, Any]]:
        record_data = {}
        for instance in model.objects.all():
            data = model_to_dict(instance)
            record_data[instance.id] = data  # type: ignore [attr-defined]
        return record_data

    def _generate_diff(self) -> None:
        for model in self.models:
            new_record_data = self._generate_record_data(model)
            added_records = []
            removed_records = []
            altered_records = {}

            for instance_id, data in self.record_data[model].items():
                if instance_id not in new_record_data:
                    removed_records.append(data)
                elif new_record_data[instance_id] != data:
                    altered_records[instance_id] = self._compare_records(
                        data,
                        new_record_data[instance_id],
                    )

            for instance_id, records in new_record_data.items():
                if instance_id not in self.record_data[model]:
                    added_records.append(records)

            self.diffs[model] = {
                "added": added_records,
                "removed": removed_records,
                "altered": altered_records,
            }

    def _compare_records(
        self,
        old_data: dict[str, Any],
        new_data: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        differences = {}
        for key in old_data:
            if old_data[key] != new_data[key]:
                differences[key] = {"old": old_data[key], "new": new_data[key]}
        return differences
