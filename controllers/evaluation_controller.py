import os
import json

from flask import Blueprint, render_template

evaluation_bp = Blueprint(
    "evaluation",
    __name__
)

@evaluation_bp.route("/evaluation")
def evaluation():

    path = "evaluation/hasil_evaluasi.json"

    if not os.path.exists(path):

        return "File hasil_evaluasi.json belum dibuat"

    with open(path, "r") as f:

        data = json.load(f)

    return render_template(
        "evaluation.html",

        total_dataset=data["total_dataset"],
        train_count=data["train"],
        test_count=data["test"],
        accuracy=data["accuracy"],

        tp=data["tp"],
        fp=data["fp"],
        fn=data["fn"],
        tn=data["tn"]
    )