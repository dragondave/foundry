import requests
r = requests.get("https://raw.githubusercontent.com/learningequality/kolibri/26073dda2569bb38bfe1e08ba486e96f650d10ce/kolibri/core/content/constants/mime.types").text

j = {}
for line in r.split("\n"):
    if line.startswith("#"):
        continue
    #if line.startswith("chemical/"):
    #    continue
    if "/x-" in line:
        continue
    if not line.strip():
        continue
    split = line.split("\t")
    if len(split) == 1:
        continue
    mime = split[0]
    ext = split[-1].split(" ")[0]
    j[mime] = ext
    
with open("mime.py", "w") as f:
    f.write("mime=" + repr(j).replace(", ", ",\n"))

