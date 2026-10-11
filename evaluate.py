import json

def load_labels(filepath="labels.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["message_id"]: item for item in data}

def load_predictions(filepath="predictions.jsonl"):
    predictions = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                predictions[item["message_id"]] = item
            except Exception as e:
                print(f"Warning: Failed to parse line {line_num}: {e}")
    return predictions

def normalize_val(val):
    if isinstance(val, str):
        return val.strip().lower()
    return val

def compare_order_ids(pred_ids, label_ids):
    p = sorted([str(x).strip().upper() for x in (pred_ids or [])])
    l = sorted([str(x).strip().upper() for x in (label_ids or [])])
    return p == l

def run_evaluation():
    labels = load_labels()
    predictions = load_predictions()

    fields = [
        "customer_name",
        "order_ids",
        "product",
        "issue_type",
        "wants_refund",
        "urgency",
        "language"
    ]

    field_correct = {f: 0 for f in fields}
    total_samples = len(labels)
    mismatches = []

    for msg_id, true_item in labels.items():
        pred_item = predictions.get(msg_id)
        if not pred_item:
            mismatches.append({
                "message_id": msg_id,
                "field": "ALL",
                "expected": "JSON object",
                "predicted": "MISSING FROM PREDICTIONS"
            })
            continue

        for field in fields:
            true_val = true_item.get(field)
            pred_val = pred_item.get(field)

            # Order IDs list comparison
            if field == "order_ids":
                is_match = compare_order_ids(pred_val, true_val)
            # Boolean comparison
            elif field == "wants_refund":
                is_match = (pred_val is true_val)
            # Text / nullable string comparison
            else:
                if true_val is None and pred_val is None:
                    is_match = True
                elif true_val is None or pred_val is None:
                    is_match = False
                else:
                    is_match = (normalize_val(pred_val) == normalize_val(true_val))

            if is_match:
                field_correct[field] += 1
            else:
                mismatches.append({
                    "message_id": msg_id,
                    "field": field,
                    "expected": true_val,
                    "predicted": pred_val
                })

    # Print Mismatches
    print("\n" + "=" * 60)
    print("DETAILED MISMATCH LOG")
    print("=" * 60)
    if not mismatches:
        print("Perfect score! No mismatches detected.")
    else:
        for m in mismatches:
            print(f"[{m['message_id']}] Field: '{m['field']}'")
            print(f"   Expected : {repr(m['expected'])}")
            print(f"   Predicted: {repr(m['predicted'])}\n")

    # Print Accuracy Table
    print("=" * 60)
    print("ACCURACY SCORECARD")
    print("=" * 60)
    print(f"{'Field':<18} | {'Correct':<8} | {'Total':<6} | {'Accuracy':<8}")
    print("-" * 60)
    for field in fields:
        correct = field_correct[field]
        pct = (correct / total_samples) * 100 if total_samples else 0
        print(f"{field:<18} | {correct:<8} | {total_samples:<6} | {pct:>6.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    run_evaluation()