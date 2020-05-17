input_file = "/analysis-data/v2Results/js-cd-results.txt"
output_file = "/analysis-data/v2Results/js-cd-results-strict.txt"

# original; alpha = 0.1, beta = 0.1, gamma = 0.4
alpha = 0.4
beta = 0.2
gamma = 0.6

with open(output_file, "w") as out_f:
    with open(input_file) as in_f:
        lines = in_f.readlines()
        for l in lines:
            line = l.strip()
            items = line.split("***")
            assert len(items) == 6
            vis_text_distance = float(items[2].strip())
            base_distance = float(items[4].strip())
            style_distance = float(items[5].strip())

            if vis_text_distance > alpha:
                if base_distance + beta < vis_text_distance:
                    if style_distance > gamma:
                        out_f.write(l)
