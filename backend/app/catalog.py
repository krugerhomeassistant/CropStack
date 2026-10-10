"""The catalog: crops, varieties, animal species and breeds, organisms and task templates (SPEC §5, §6.1, §16.1).

Three layers, later ones winning field by field:
1. bundled  `catalog/` in the repo (CC BY-SA 4.0), every value cited and licence-checked;
2. private  `<data>/catalog-private/` on the owner's server: same format, never committed or shipped, for values
   looked up for personal use from any source; no licence gate;
3. household overrides in the database (`catalogoverride`), edited in the app.

The catalog is read from YAML into memory at startup (it is read-only and small); only overrides live in the DB.
Models here are the single source of the format; `scripts/catalog_schema.py` writes JSON Schema files from them.
"""

from __future__ import annotations

import copy
import hashlib
from datetime import date
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

Evidence = Literal["peer-reviewed", "government", "extension-service", "model", "grower-reported", "traditional"]
Kind = Literal["crop", "variety", "species", "breed", "organism", "task_template"]
KINDS: tuple[Kind, ...] = ("crop", "variety", "species", "breed", "organism", "task_template")
PARENT_KIND: dict[str, Kind] = {"variety": "crop", "breed": "species"}

# Licences whose material may be bundled in the public catalog (CC BY-SA 4.0 accepts all of these).
OPEN_LICENCES = {"CC0-1.0", "PD", "US-PD", "CC-BY-4.0", "CC-BY-SA-4.0", "BSD-3-Clause", "EPPO-Open-Data"}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- provenance


class SourceRef(Strict):
    ref: str  # id in catalog/sources.yaml
    retrieved: date | None = None
    locator: str | None = None  # "Table 1", "p. 12", a URL fragment
    snapshot: str | None = None  # "sha256:…" of the raw copy kept outside git


class Range(Strict):
    """Limits of a variable: absolute min and max, and the best value `opt` or the best band `opt_min`..`opt_max`."""

    min: float | None = None
    opt_min: float | None = None
    opt: float | None = None
    opt_max: float | None = None
    max: float | None = None

    @model_validator(mode="after")
    def ordered(self) -> Range:
        vals = [v for v in (self.min, self.opt_min, self.opt, self.opt_max, self.max) if v is not None]
        if not vals:
            raise ValueError("a range needs at least one of min, opt_min, opt, opt_max, max")
        if vals != sorted(vals):
            raise ValueError("range must satisfy min <= opt_min <= opt <= opt_max <= max")
        return self


class Value(Strict):
    """One cited fact (SPEC §16.1). Conflicting sources become separate qualified Values, never an average."""

    value: Range | float | bool | str
    unit: str | None = None  # UCUM-style: Cel, mm, cm, d, h, %, m2, kg/m2
    qualifiers: dict[str, str | float | None] = Field(default_factory=dict)
    evidence: Evidence
    confidence: Literal["high", "medium", "low"] = "medium"
    rank: Literal["preferred", "normal", "deprecated"] = "normal"
    estimate: bool = False  # an informed estimate with no source; must say so
    sources: list[SourceRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def cited(self) -> Value:
        if not self.sources and not self.estimate:
            raise ValueError("every value needs a source, or estimate: true")
        return self


Fact = Value | list[Value]  # several qualified statements (e.g. per region) are a list


# ---------------------------------------------------------------- requirement profile (SPEC §5)


class Temperature(Strict):
    lethal_min: Fact | None = None  # °C: damage/death below (frost tolerance)
    stress_min: Fact | None = None  # growth stops / chilling injury
    optimal: Fact | None = None  # range of best growth
    stress_max: Fact | None = None  # heat stress (bolting, flower drop, reduced lay)
    lethal_max: Fact | None = None
    base: Fact | None = None  # growing-degree-day base
    upper_cutoff: Fact | None = None  # growing-degree-day upper cutoff


class SoilTemperature(Strict):
    germination: Fact | None = None  # range min / opt / max


class Photoperiod(Strict):
    response: Fact | None = None  # short_day | long_day | neutral
    critical_hours: Fact | None = None


class Vernalization(Strict):
    required: Fact | None = None
    below_c: Fact | None = None
    hours_needed: Fact | None = None


class Chill(Strict):
    model: Fact | None = None  # dynamic | utah | hours_below_7
    required: Fact | None = None


class Water(Strict):
    kc_initial: Fact | None = None
    kc_mid: Fact | None = None
    kc_late: Fact | None = None
    root_depth: Fact | None = None
    depletion_fraction: Fact | None = None
    drought_tolerance: Fact | None = None  # low | medium | high
    waterlogging_tolerance: Fact | None = None


class Humidity(Strict):
    disease_risk_rh: Fact | None = None
    thi_alert: Fact | None = None  # animals: temperature-humidity index
    thi_danger: Fact | None = None


class Light(Strict):
    min_sun_hours: Fact | None = None


class Soil(Strict):
    ph: Fact | None = None
    drainage: Fact | None = None


class Requirements(Strict):
    temperature: Temperature = Field(default_factory=Temperature)
    soil_temperature: SoilTemperature = Field(default_factory=SoilTemperature)
    photoperiod: Photoperiod = Field(default_factory=Photoperiod)
    vernalization: Vernalization = Field(default_factory=Vernalization)
    chill: Chill = Field(default_factory=Chill)
    water: Water = Field(default_factory=Water)
    humidity: Humidity = Field(default_factory=Humidity)
    wind_max: Fact | None = None
    light: Light = Field(default_factory=Light)
    soil: Soil = Field(default_factory=Soil)


# ---------------------------------------------------------------- items

Slug = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=80)]
Names = dict[str, list[str]]  # language code -> names, first is the display name: {"en": ["Tomato"], "af": ["Tamatie"]}


class Item(Strict):
    kind: Kind
    slug: Slug
    names: Names
    description: str | None = None  # written fresh for CropStack, never copied (SPEC §16.1)
    requirements: Requirements = Field(default_factory=Requirements)
    # Kind-specific parameters (spacing, depth, days to maturity, gestation, identification…). Phase 5/9 content
    # gives these typed fields once their engines need them.
    params: dict[str, Fact] = Field(default_factory=dict)


class Crop(Item):
    kind: Literal["crop"]
    scientific_name: str
    family: str  # APG IV family, e.g. Solanaceae
    rotation_group: str | None = None
    life_cycle: Literal["annual", "biennial", "perennial"]


class Variety(Item):
    kind: Literal["variety"]
    parent: Slug  # crop slug; any field set here overrides the crop's


class Species(Item):
    kind: Literal["species"]
    scientific_name: str


class Breed(Item):
    kind: Literal["breed"]
    parent: Slug  # species slug


class Organism(Item):
    kind: Literal["organism"]
    organism_type: Literal["pest", "disease", "beneficial", "pollinator", "weed", "deficiency"]
    scientific_name: str | None = None
    hosts: list[Slug] = Field(default_factory=list)  # crop slugs it affects; empty = any crop


class TaskTemplate(Item):
    """How to do a kind of job, in plain steps (written fresh for CropStack, shown under each job on Today)."""

    kind: Literal["task_template"]
    applies_to: list[Kind]
    task_kind: Literal[
        "sow", "set_out", "harvest", "water", "frost", "heat", "check"
    ]  # the engine's job kind it explains
    steps: list[str] = Field(min_length=1)


MODELS: dict[str, type[Item]] = {
    "crop": Crop,
    "variety": Variety,
    "species": Species,
    "breed": Breed,
    "organism": Organism,
    "task_template": TaskTemplate,
}


class Source(Strict):
    id: Slug
    title: str
    author: str | None = None
    url: str
    license: str  # SPDX-like id, or a short description for closed sources
    use: Literal["bundle", "facts-only", "link-only"]
    extra_terms: str | None = None
    tos_reviewed: date
    access: Literal["api", "bulk-download", "html-scrape", "manual"] = "manual"

    @model_validator(mode="after")
    def bundle_needs_open_licence(self) -> Source:
        if self.use == "bundle" and self.license not in OPEN_LICENCES:
            raise ValueError(f"licence {self.license!r} can't be bundled; use facts-only or link-only")
        return self


# ---------------------------------------------------------------- loading


class CatalogError(Exception):
    pass


class Catalog:
    """Loaded catalog: items by (kind, slug) with their origin, plus the source registry."""

    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict[str, Any]] = {}  # merged bundled + private data
        self.origin: dict[tuple[str, str], str] = {}  # bundled | private | bundled+private
        self.sources: dict[str, Source] = {}
        self.version = ""  # hash of the bundled files
        self.private_errors: list[str] = []

    def get(self, kind: str, slug: str) -> dict[str, Any] | None:
        return self.items.get((kind, slug))

    def list(self, kind: str) -> list[tuple[str, dict[str, Any]]]:
        return sorted((slug, data) for (k, slug), data in self.items.items() if k == kind)


def _read_items(root: Path) -> tuple[list[tuple[Path, dict]], list[str]]:
    docs, errors = [], []
    for path in sorted(root.glob("**/*.yaml")):
        if path.name == "sources.yaml":
            continue
        try:
            data = yaml.safe_load(path.read_text())
        except yaml.YAMLError as e:
            errors.append(f"{path}: not valid YAML: {e}")
            continue
        if not isinstance(data, dict) or data.get("kind") not in MODELS:
            errors.append(f"{path}: needs a mapping with kind: one of {', '.join(KINDS)}")
            continue
        docs.append((path, data))
    return docs, errors


def _validate(path: Path, data: dict) -> str | None:
    try:
        MODELS[data["kind"]].model_validate(data)
    except ValidationError as e:
        return f"{path}: {e}"
    return None


def load(bundled_root: Path, private_root: Path | None = None) -> Catalog:
    """Load and check the bundled catalog (any problem raises), then the private pack (problems are collected
    in catalog.private_errors so a typo on the owner's server never stops the app)."""
    cat = Catalog()
    sources_file = bundled_root / "sources.yaml"
    raw_sources = yaml.safe_load(sources_file.read_text()) if sources_file.exists() else []
    errors: list[str] = []
    for entry in raw_sources or []:
        try:
            source = Source.model_validate(entry)
        except ValidationError as e:
            errors.append(f"{sources_file}: {e}")
            continue
        if source.id in cat.sources:
            errors.append(f"{sources_file}: duplicate source id {source.id}")
        cat.sources[source.id] = source

    docs, read_errors = _read_items(bundled_root)
    errors += read_errors
    digest = hashlib.sha256()
    for path, data in docs:
        digest.update(path.read_bytes())
        if problem := _validate(path, data) or _licence_problem(path, data, cat.sources):
            errors.append(problem)
            continue
        key = (data["kind"], data["slug"])
        if key in cat.items:
            errors.append(f"{path}: duplicate {key[0]} slug {key[1]}")
        cat.items[key] = data
        cat.origin[key] = "bundled"
    errors += _parent_problems(cat)
    if errors:
        raise CatalogError("Bundled catalog is invalid:\n" + "\n".join(errors))
    cat.version = digest.hexdigest()[:12]

    if private_root and private_root.is_dir():
        docs, cat.private_errors = _read_items(private_root)
        for path, data in docs:
            key = (data["kind"], data.get("slug", ""))
            merged = deep_merge(cat.items.get(key, {}), data)
            if problem := _validate(path, merged):
                cat.private_errors.append(problem)
                continue
            cat.origin[key] = "bundled+private" if key in cat.items else "private"
            cat.items[key] = merged
        cat.private_errors += _parent_problems(cat, only_private=True)
    return cat


def _licence_problem(path: Path, data: dict, sources: dict[str, Source]) -> str | None:
    """Every value in the bundled catalog cites a registered source that may be used for it."""
    for ref in _source_refs(data):
        source = sources.get(ref)
        if source is None:
            return f"{path}: cites unknown source {ref!r} (add it to sources.yaml)"
        if source.use == "link-only":
            return f"{path}: cites {ref!r}, which may only be linked to, not used as data"
    return None


def _source_refs(node: Any):
    if isinstance(node, dict):
        if "evidence" in node and "sources" in node:
            for s in node["sources"] or []:
                yield s.get("ref")
        else:
            for v in node.values():
                yield from _source_refs(v)
    elif isinstance(node, list):
        for v in node:
            yield from _source_refs(v)


def _parent_problems(cat: Catalog, only_private: bool = False) -> list[str]:
    problems = []
    for (kind, slug), data in cat.items.items():
        if only_private and cat.origin[(kind, slug)] == "bundled":
            continue
        parent_kind = PARENT_KIND.get(kind)
        if parent_kind and (parent_kind, data["parent"]) not in cat.items:
            problems.append(f"{kind} {slug}: parent {parent_kind} {data['parent']!r} not found")
    return problems


# ---------------------------------------------------------------- merging & overrides


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """overlay wins field by field; nested mappings merge, everything else (values, lists) is replaced."""
    out = copy.deepcopy(base)
    for k, v in overlay.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def set_path(data: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    out = copy.deepcopy(data)
    node = out
    *parents, leaf = path.split(".")
    for part in parents:
        node = node.setdefault(part, {})
        if not isinstance(node, dict):
            raise CatalogError(f"{path}: {part} is not a section")
    node[leaf] = value
    return out


def effective(cat: Catalog, kind: str, slug: str, overrides: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """An item as one household sees it: parent (for varieties/breeds), item, then household overrides."""
    data = cat.get(kind, slug)
    if data is None:
        return None
    parent_kind = PARENT_KIND.get(kind)
    if parent_kind and (parent := cat.get(parent_kind, data["parent"])):
        inherited = {k: v for k, v in parent.items() if k in ("requirements", "params")}
        data = deep_merge(inherited, data)
    for path, value in (overrides or {}).items():
        data = set_path(data, path, value)
    return data


def check_overrides(cat: Catalog, kind: str, slug: str, overrides: dict[str, Any]) -> None:
    """Raise CatalogError unless the item stays valid with all these overrides applied."""
    data = cat.get(kind, slug)
    if data is None:
        raise CatalogError(f"no {kind} {slug!r}")
    for path, value in overrides.items():
        if path.split(".")[0] in ("kind", "slug", "parent"):
            raise CatalogError("kind, slug and parent can't be overridden")
        data = set_path(data, path, value)
    try:
        MODELS[kind].model_validate(data)
    except ValidationError as e:
        raise CatalogError(str(e)) from e
