def get_tag_structure(tags):
    output = []
    for tag in tags:
        output.append({"Key": tag, "Value": tags[tag]})

    return output
