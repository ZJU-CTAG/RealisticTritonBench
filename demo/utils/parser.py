import re


# Other tests:
# 30974: "python examples/offline_inference/vision_language.py -m gemma3 --num-prompts 1"


def _process(result):
    return {}

def result_parser(merged_result):
    pytest_res, acc_res, latency_res, other_res = [], {}, {}, []

    # 1. Parse pytest results
    if merged_result["unit_tests_result"] != []:

        for result in merged_result["unit_tests_result"]:
            output = result["output"]

            m_passed = re.search(r"(\d+)\s+passed", output)
            if m_passed:
                passed = int(m_passed.group(1))
            
            not_passed = 0
            for key in ["failed", "skipped", "error", "errors", "xfailed", "xpassed"]:
                m = re.search(r"(\d+)\s+" + key, output)
                if m:
                    not_passed += int(m.group(1))

            pytest_res.append({
                "test_id": result["test_id"],
                "passed": passed,
                "failed": not_passed
            })

    # 2. Parse model accuracy results
    if merged_result["accuracy_test_result"]:
        output = merged_result["accuracy_test_result"]["output"]

        in_table = False

        acc_res = {
            "test_id": merged_result["accuracy_test_result"]["test_id"],
        }
        task_name = None

        for line in output.splitlines():
            if 'Tasks' in line and 'Version' in line:
                in_table = True
                continue

            if in_table:
                if 'exact_match' in line:
                    cols = line.split('|')
                    if len(cols) >= 9:
                        if cols[1].strip() != "":
                            task_name = cols[1].strip()
                        filter_name = cols[3].strip()
                        try:
                            value = float(cols[7].strip())
                        except ValueError:
                            value = None
                        if task_name:
                            acc_res["dataset"] = task_name
                        acc_res[filter_name] = value
                elif not line.startswith('|'):
                    break
        assert acc_res != {}, "[ERROR] accuracy results parse failed"

    # 3. Parse latency test results
    if merged_result["latency_test_result"]:
        output = merged_result["latency_test_result"]["output"]

        match = re.search(r"=+\s*Serving Benchmark Result\s*=+\n(.*)", output, re.DOTALL)
        if match:
            result_text = match.group(1)
            
            # 定义一个小函数方便提取 float
            def extract_value(key, text):
                m = re.search(rf"{re.escape(key)}:\s*([0-9.]+)", text)
                return float(m.group(1)) if m else None

            latency_res = {
                "test_id": merged_result["latency_test_result"]["test_id"],
                "ttft": extract_value("Mean TTFT (ms)", result_text),
                "tpot": extract_value("Mean TPOT (ms)", result_text),
                "output_throughput": extract_value("Output token throughput (tok/s)", result_text),
                "total_throughput": extract_value("Total Token throughput (tok/s)", result_text),
            }
        else:
            raise Exception("[ERROR] latency results parse failed")
    # 4. Parse other tests results
    if merged_result["other_tests_result"] != []:
        for result in merged_result["other_tests_result"]:
            res = _process(result)
            other_res.append(res)

    return pytest_res, acc_res, latency_res, other_res