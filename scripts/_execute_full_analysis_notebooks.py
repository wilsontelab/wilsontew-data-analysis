import json
from pathlib import Path

nb_paths = [
    Path(r"c:\Users\dunnmk\wilsontew-data-analysis\notebooks\full_analysis_notebooks\ThreeC_OneShot_Report.ipynb"),
    Path(r"c:\Users\dunnmk\wilsontew-data-analysis\notebooks\full_analysis_notebooks\ThreeC_OneShot_Report_captioned.ipynb"),
    Path(r"c:\Users\dunnmk\wilsontew-data-analysis\notebooks\full_analysis_notebooks\PD_OneShot_Report.ipynb"),
    Path(r"c:\Users\dunnmk\wilsontew-data-analysis\notebooks\full_analysis_notebooks\PD_3C_4C_Combined_Report.ipynb"),
    Path(r"c:\Users\dunnmk\wilsontew-data-analysis\notebooks\full_analysis_notebooks\FourC_OneShot_Python_Report.ipynb"),
    Path(r"c:\Users\dunnmk\wilsontew-data-analysis\notebooks\full_analysis_notebooks\FourC_Joey_Filtered.ipynb"),
    Path(r"c:\Users\dunnmk\wilsontew-data-analysis\notebooks\full_analysis_notebooks\FourC_Q1_Filtered_Analysis.ipynb"),
    Path(r"c:\Users\dunnmk\wilsontew-data-analysis\notebooks\full_analysis_notebooks\FourC_Q1_Q2_Filtered_Analysis.ipynb"),
]

report = []

try:
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError
except Exception as e:
    print("IMPORT_ERROR:", repr(e))
    raise

for p in nb_paths:
    item = {"notebook": str(p), "status": "PASS", "error": None}
    if not p.exists():
        item["status"] = "FAIL"
        item["error"] = "File not found"
        report.append(item)
        continue

    try:
        nb = nbformat.read(str(p), as_version=4)
        client = NotebookClient(nb, timeout=1800, kernel_name=None, resources={"metadata": {"path": str(p.parent)}})
        client.execute()
        nbformat.write(nb, str(p))
    except CellExecutionError as e:
        item["status"] = "FAIL"
        item["error"] = str(e)
        try:
            nbformat.write(nb, str(p))
        except Exception:
            pass
    except Exception as e:
        item["status"] = "FAIL"
        item["error"] = repr(e)
    report.append(item)

out = Path(r"c:\Users\dunnmk\wilsontew-data-analysis\Outputs\full_analysis_notebook_execution_report.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")

print(json.dumps(report, indent=2))
print(f"\nWROTE_REPORT={out}")
