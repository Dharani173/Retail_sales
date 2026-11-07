import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt

REQUIRED = ["date", "product", "category", "region", "quantity", "unit_price"]
DATE_FORMATS = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
                "%Y/%m/%d", "%d-%b-%Y", "%d %b %Y"]


# ---------------------------------------------------------------
# 1. Ask the user to choose a CSV file
# ---------------------------------------------------------------
def choose_file():
    # Option A: file path given in the command line
    if len(sys.argv) > 1:
        return sys.argv[1]

    # Option B: file upload window (tkinter comes with Python)
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Select your sales CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        root.destroy()
        return path
    except Exception:
        # Option C: type the path if the window cannot open
        return input("Type the full path of your CSV file: ").strip().strip('"')


# ---------------------------------------------------------------
# 2. Read the CSV file
# ---------------------------------------------------------------
def parse_date(text):
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def clean_number(text):
    return float(str(text).replace(",", "").replace("Rs.", "").replace("₹", "").strip())


def load_data(path):
    records, skipped = [], 0

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("The CSV file is empty.")

        # make column names simple: "Unit Price" -> "unit_price"
        names = {h: h.strip().lower().replace(" ", "_") for h in reader.fieldnames}
        missing = [c for c in REQUIRED if c not in names.values()]
        if missing:
            raise ValueError("Missing column(s): " + ", ".join(missing) +
                             "\nYour file has: " + ", ".join(reader.fieldnames))

        for raw in reader:
            row = {names[k]: (v or "").strip() for k, v in raw.items() if k in names}
            try:
                when = parse_date(row["date"])
                qty = clean_number(row["quantity"])
                price = clean_number(row["unit_price"])
                if when is None or not row["product"]:
                    raise ValueError
                records.append({
                    "Month": when.strftime("%Y-%m"),
                    "Product": row["product"],
                    "Category": row["category"] or "Unknown",
                    "Region": row["region"] or "Unknown",
                    "Quantity": qty,
                    "Total": qty * price,
                })
            except (ValueError, TypeError):
                skipped += 1

    return records, skipped


def total_by(records, key):
    totals = defaultdict(float)
    for r in records:
        totals[r[key]] += r["Total"]
    return dict(totals)


# ---------------------------------------------------------------
# 3. Print the summary
# ---------------------------------------------------------------
def print_summary(records, skipped, filename):
    revenue = sum(r["Total"] for r in records)
    units = sum(r["Quantity"] for r in records)
    best_product = max(total_by(records, "Product").items(), key=lambda x: x[1])[0]
    best_region = max(total_by(records, "Region").items(), key=lambda x: x[1])[0]

    print("\n========== SALES SUMMARY ==========")
    print(f"File               : {os.path.basename(filename)}")
    print(f"Total Revenue      : Rs. {revenue:,.0f}")
    print(f"Total Orders       : {len(records)}")
    print(f"Units Sold         : {units:,.0f}")
    print(f"Average Order Value: Rs. {revenue / len(records):,.0f}")
    print(f"Best Product       : {best_product}")
    print(f"Best Region        : {best_region}")
    if skipped:
        print(f"Rows skipped (bad data): {skipped}")
    print("===================================\n")


# ---------------------------------------------------------------
# 4. Draw the dashboard
# ---------------------------------------------------------------
def show_dashboard(records, image_path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Retail Sales Dashboard", fontsize=20, fontweight="bold")

    monthly = total_by(records, "Month")
    months = sorted(monthly)
    axes[0][0].plot(months, [monthly[m] for m in months], marker="o", color="teal")
    axes[0][0].set_title("Monthly Sales Trend")
    axes[0][0].set_ylabel("Sales (Rs.)")
    axes[0][0].tick_params(axis="x", rotation=45)
    axes[0][0].grid(alpha=0.3)

    cat = total_by(records, "Category")
    names = sorted(cat, key=cat.get, reverse=True)
    axes[0][1].bar(names, [cat[n] for n in names], color="steelblue")
    axes[0][1].set_title("Sales by Category")
    axes[0][1].set_ylabel("Sales (Rs.)")
    axes[0][1].tick_params(axis="x", rotation=30)

    reg = total_by(records, "Region")
    axes[1][0].pie(list(reg.values()), labels=list(reg.keys()),
                   autopct="%1.1f%%", startangle=90)
    axes[1][0].set_title("Sales Share by Region")

    prod = total_by(records, "Product")
    top5 = sorted(prod, key=prod.get, reverse=True)[:5][::-1]
    axes[1][1].barh(top5, [prod[p] for p in top5], color="purple")
    axes[1][1].set_title("Top 5 Products by Sales")
    axes[1][1].set_xlabel("Sales (Rs.)")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(image_path, dpi=150)
    print("Dashboard image saved as:", image_path)
    plt.show()


# ---------------------------------------------------------------
# Main program
# ---------------------------------------------------------------
def main():
    path = choose_file()
    if not path:
        print("No file selected. Program closed.")
        return
    if not os.path.isfile(path):
        print("File not found:", path)
        return

    try:
        records, skipped = load_data(path)
    except Exception as error:
        print("\nCould not read the file:\n", error)
        return

    if not records:
        print("No valid rows found. Check your Date, Quantity and Unit_Price values.")
        return

    print_summary(records, skipped, path)
    image_path = os.path.join(os.path.dirname(os.path.abspath(path)),
                              "sales_dashboard.png")
    show_dashboard(records, image_path)


if __name__ == "__main__":
    main()