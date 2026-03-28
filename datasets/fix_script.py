with open("conl_data_label.conll", "r") as fin, open("cleaned_conll.conll", "w") as fout:
    for line in fin:
        stripped = line.strip()
        if not stripped:
            fout.write("\n")  
            continue
        parts = stripped.split()
        if len(parts) < 4:
            while len(parts) < 3:
                parts.append("-X-")
            parts.append("O")
        elif parts[-1] == "_":
            parts[-1] = "O"
        fout.write(" ".join(parts) + "\n")

