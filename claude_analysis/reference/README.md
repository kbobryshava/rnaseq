# nf-core/rnaseq 3.27.0 – directed software-relationship reference dataset (frozen)

A reference set of **directed software relationships** extracted from the nf-core/rnaseq workflow code, with positive controls, negative controls and a separate layer of non-data (gate / parameter) dependencies, each backed by process-level evidence and source file:line references.

**Definition.** Software A → B means: data produced by a process that runs A is consumed, as an input channel of a process that runs B. Not inferred from source order, diagram proximity, shared workflow membership, co-occurrence or shared inputs; no transitive closure.

| | |
|---|---|
| Pipeline | nf-core/rnaseq **3.27.0**, commit `a1fcdddd3b826fe46eb46f0479f2ff8a7815af05` (see `MANIFEST.json`) |
| Analysis | local, static (Nextflow source + `nextflow -preview` DAGs); **no workflow was executed** |
| Original nf-core files | unchanged |
| Validation | `VALIDATION_SUMMARY.md` (machine-readable: `validation.json`) |
| Integrity | `SHA256SUMS`, `MANIFEST.json` |

## Which file do I use?

Software level (`software_level/`, one row per ordered software pair):

| file | records | meaning |
|---|---|---|
| `gold_positive_controls.csv` | 203 | real data flow verified in the source, both ends named tools. 29 verified pair by pair (`verification_level = pair`), 174 verified per workflow family (`family-rule`, see METHODOLOGY §6) |
| `silver_positive_controls.csv` | 91 | real data flow, but an end is a generic utility / local script (tar, gzip, cat, sed, gawk, nf-core custom Python scripts) or only part of the payload is used. 22 pair, 69 family-rule |
| `negative_controls_verified.csv` | 56 | not a data exchange, confirmed by reading the source: 2 extractor false positives, sibling QC tools on the same BAM (Preseq, Qualimap, dupRadar, featureCounts, RSeQC, StringTie, BEDTools), RustQC vs the other QC tools (`use_rustqc`), FastQC vs Trim Galore, fastp vs Trim Galore, Parabricks vs Sentieon STAR |
| `negative_candidates_unverified.csv` | 229 | algorithmically identified negatives (no path in the extracted graph, shared input, reverse of a positive, rule-based artifacts). **Not verified one by one.** |
| `dependencies_gate_metadata.csv` | 41 | functional dependencies that are *not* data payloads: STAR/aligner percent-mapped gate (24), Salmon-inferred strandedness that sets parameters (8), other gates (9). Neither positive nor negative controls; use them as a separate "parameter/gating" layer |
| `algorithmic_supported_pairs.csv` | 46 | extracted, not adjudicated: 14 self-loops and 32 reporting-only (MultiQC) pairs. No analysis pair is left unadjudicated. |
| `software_relationships_all.csv` / `.parquet` | 666 | all of the above, column `category` |

Process level (`process_level/`, one row per process-instance edge; 1,234 edges):

| `validation_category` | records | meaning |
|---|---|---|
| `source_verified_positive` | 685 | supporting edges of the Gold/Silver pairs (115 read pair by pair, 570 by family rule: column `verification_level`) |
| `source_verified_negative` | 5 | verified extractor artifacts / infeasible paths |
| `algorithmic_supported` | 244 | extracted, not rejected, not adjudicated (reporting aggregation into MultiQC, self-loops, ...) |
| `algorithmic_negative_candidate` | 172 | rejected by the payload check (78) or key-only synchronisation (94) |
| `functional_dependency_non_data` | 128 | gate / metadata edges |

`process_relationships_all.csv` (+ `.parquet`) holds all rows; the other CSVs are subsets. Software rows list their `process_edge_ids`, so every software pair can be traced to its edges, processes, operations and `file:line`.

## Quick start (Python)

```python
import pandas as pd
sw = pd.read_csv("claude_analysis/reference/software_level/software_relationships_all.csv")
gold = sw[sw.category == "Gold"]
neg  = sw[sw.category == "Negative_verified"]
gold_pair_level = gold[gold.verification_level == "pair"]      # the 29 individually adjudicated pairs
pe   = pd.read_csv("claude_analysis/reference/process_level/process_relationships_all.csv")
edges_of_pair = pe[pe.edge_id.isin(gold.iloc[0].process_edge_ids.split(";"))]
```

## Reproduce from a clean checkout

```bash
git clone --branch claude/directed-software-analysis-3.27.0 https://github.com/kbobryshava/rnaseq.git
cd rnaseq
pip install -r claude_analysis/requirements.txt          # Python >= 3.10 (3.13 used)
bash claude_analysis/scripts/reproduce_all.sh             # ~1 min, pure Python
cd claude_analysis/reference && sha256sum -c SHA256SUMS   # byte-identical CSVs/reports
```
Re-generating the preview DAGs (`--with-previews`) additionally needs Java 17 and Nextflow (they were produced with Nextflow 26.10.5 in WSL); the committed DAGs in `data/raw/` are the recorded inputs (hashes in `MANIFEST.json`).

## Read this before using it as a benchmark

* Gold/Silver mean **verified by reading the source**, not observed running. **Parameter policy.** A relationship counts whenever the two tools *can* be used together in some valid parameter combination, whether or not it is the default. `required_params` records the options that activate it and `in_default_test_profile` says whether it also appears in the default `-profile test` run; neither affects the category. Only combinations the pipeline itself forbids (e.g. `--use_parabricks_star` with `--use_sentieon_star`) are excluded.
* **Software identity ≠ operation performed.** Always read `source_operations` / `target_operations`. Example: *RSEM → kallisto* is `rsem-prepare-reference` used only to extract the transcriptome FASTA that `kallisto index` consumes; it has nothing to do with RSEM quantification.
* Software nodes collapse several processes (SAMtools: 9 operations; "nf-core custom script (Python)": several distinct scripts). Software-level graphs contain cycles that do not exist at process level (the process graph is acyclic).
* **How the positives were verified.** 29 Gold and 22 Silver pairs were adjudicated one by one. The other 174 Gold and 69 Silver pairs were adjudicated by *workflow family* (reads pre-processing chain, BAM chain, unaligned-reads screening, reference resources, RSEM downstream): the family's channel structure was read once, and a pair is included only if the extractor has a live edge of that family whose stage order is valid. Filter on `verification_level == "pair"` for the strictest set.
* The positive set is complete only relative to the extractor (it is not a recall estimate); flows the extractor cannot see are missing.
* Unverified negatives assert absence of a path in the *extracted* graph. Gate/parameter dependencies (strandedness inference, percent-mapped filter) are kept in their own category, not mixed into the controls.
* One reviewer (an AI assistant working from the source); no independent human second review yet. A bioinformatician should review at least the 29 pair-level Gold pairs and a sample of the family-rule pairs. See `METHODOLOGY.md` §8.
