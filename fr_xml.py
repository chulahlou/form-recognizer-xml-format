import json

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

AZ_ENDPOINT = ""
AZ_KEY = ""


def call_fr_api(file_name):
    document_analysis_client = DocumentAnalysisClient(
        endpoint=AZ_ENDPOINT, credential=AzureKeyCredential(AZ_KEY)
    )
    with open(f"docs/{file_name}.pdf", "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-document", f)
    api_result = poller.result()
    return api_result


def format_result_as_xml(data):
    def _make_placement_attrs(p):
        brs = p["bounding_regions"][0]["polygon"]
        x = [br["x"] for br in brs]
        y = [br["y"] for br in brs]
        left, top = min(x), min(y)
        width = abs(min(x) - max(x))
        height = abs(min(y) - max(y))
        return f"""left="{left:.5}" top="{top:.5}" width="{width:.5}" height="{height:.5}" """

    is_title_open = False
    is_subheading_open = False

    xml = ""
    for p in data["paragraphs"]:
        role = p["role"]
        placement_str = _make_placement_attrs(p)
        if role == "pageHeader":
            xml_line = f"""<p type="pageHeader" page="{p['bounding_regions'][0]['page_number']}" {placement_str}>{p['content']}</p>"""
        elif role == "pageFooter":
            xml_line = f"""<p type="pageFooter" page="{p['bounding_regions'][0]['page_number']}" {placement_str}>{p['content']}</p>"""
        elif role == "footnote":
            xml_line = f"""<p type="footnote" page="{p['bounding_regions'][0]['page_number']}" {placement_str}>{p['content']}</p>"""
        elif role == "title":
            xml_line = ""
            if is_title_open:
                xml_line = """</section> \n"""
            if is_subheading_open:
                xml_line = """</section> </section> \n"""
                is_subheading_open = False
            xml_line += f"""<section level="1" page="{p['bounding_regions'][0]['page_number']}" {placement_str}> \n"""
            xml_line += f"""<header>{p['content']}</header>"""
            is_title_open = True
        elif role == "sectionHeading":
            xml_line = ""
            if is_subheading_open:
                xml_line = """</section> \n"""
            if not is_title_open:
                xml_line += "<section>\n"
                is_title_open = True
            xml_line += f"""<section level="2" page="{p['bounding_regions'][0]['page_number']}" {placement_str}>{p['content']}> \n"""
            xml_line += f"""<header>{p['content']}</header>"""
            is_subheading_open = True
        else:
            xml_line = f"""<p page="{p['bounding_regions'][0]['page_number']}" {placement_str}>{p['content']}</p>"""
        xml += xml_line + "\n"

    if is_subheading_open:
        xml += "</section>\n"
    if is_title_open:
        xml += "</section>\n"

    return "<root>\n" + xml + "</root>"


if __name__ == "__main__":
    file_name = "Sample-Amendment"

    # result = call_fr_api(file_name)
    # result = result.to_dict()

    # Store as JSON result
    # with open(f"docs/{file_name}.json", "w") as f:
    #     json.dump(result, f, indent=4)

    # Load from stored JSON results
    with open(f"docs/{file_name}.json", "r") as f:
        result = json.load(f)

    xml = format_result_as_xml(result)

    with open(f"docs/{file_name}.xml", "w") as f:
        f.write(xml)

    # Use a formatter e.g. https://jsonformatter.org/xml-formatter to get nice spacing
