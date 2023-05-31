from typing import Any, Literal, cast, Type
from django.db.models import Model
from django.forms.models import model_to_dict

from ..bit import Bit

# from .serializers import QuerySerializer, RequestResponseSerializer, TestInfoSerializer


class DatabaseDiff(Bit):
    """ """

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        models = kwargs.pop("models", None)

        super().__init__(*args, **kwargs)
        self.models = cast(list[Type[Model]], models or getattr(self, "models", []))
        self.record_data: dict[Type[Model], dict[int, dict[str, Any]]] = {}
        self.diffs: dict[Type[Model], dict[str, list[Any]]] = {}

    def __enter__(self):
        for model in self.models:
            self.record_data[model] = self._generate_record_data(model)

    def __exit__(self, *args: Any) -> Literal[False]:
        self._generate_diff()
        return False

    @property
    def data(self) -> dict[str, Any]:
        result = {
            "models": {
                model.__name__: {
                    "added": self.diffs[model]["added"],
                    "removed": self.diffs[model]["removed"],
                    "altered": self.diffs[model]["altered"],
                }
                for model in self.models
            }
        }
        breakpoint()
        return result

    def _generate_record_data(self, model: Type[Model]) -> dict[int, dict[str, Any]]:
        record_data = {}
        for instance in model.objects.all():
            data = model_to_dict(instance)
            record_data[instance.id] = data
        return record_data

    def _generate_diff(self) -> None:
        for model in self.models:
            new_record_data = self._generate_record_data(model)
            added_records = []
            removed_records = []
            altered_records = {}

            for id, data in self.record_data[model].items():
                if id not in new_record_data:
                    removed_records.append(data)
                elif new_record_data[id] != data:
                    altered_records[id] = self._compare_records(
                        data, new_record_data[id]
                    )

            for id in new_record_data:
                if id not in self.record_data[model]:
                    added_records.append(new_record_data[id])

            self.diffs[model] = {
                "added": added_records,
                "removed": removed_records,
                "altered": altered_records,
            }

    def _compare_records(
        self, old_data: dict[str, Any], new_data: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        differences = {}
        for key in old_data:
            if old_data[key] != new_data[key]:
                differences[key] = {"old": old_data[key], "new": new_data[key]}
        return differences
