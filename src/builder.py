#!/usr/bin/env python3

import json
import datetime
import os

from logger import Logger
from conf import BRANCHES, ROOT_FOLDER, OUTPUT_FOLDER


class Builder():
    """Handle generation of output files"""

    def __init__(self, states, countries):
        self.logger = Logger()
        self.states = states
        self.countries = countries
        self.check_folder()
        self.json_path = ROOT_FOLDER + OUTPUT_FOLDER + "status.json"
        self.html_path = ROOT_FOLDER + OUTPUT_FOLDER + "index.html"

    def check_folder(self):
        """Check if output folder exists"""
        try:
            if not os.path.isdir(ROOT_FOLDER + OUTPUT_FOLDER):
                os.makedirs(ROOT_FOLDER + OUTPUT_FOLDER)
        except OSError as e:
            self.logger.error("can't create output folder", e)

    def generate_output(self):
        """Generate all output files"""
        self.write_json_output()
        self.write_html_output()

    def write_json_output(self):
        """Generate JSON output"""
        try:
            with open(self.json_path, "w") as json_output:
                json.dump(self.states, json_output, sort_keys=True)
                self.logger.info("JSON output generated")
        except OSError as e:
            self.logger.error("can't write JSON output", e)

    def write_html_output(self):
        """Generate HTML output"""
        try:
            with open(ROOT_FOLDER + "data/header.html", "r") as header_file:
                header = header_file.read()
            with open(ROOT_FOLDER + "data/footer.html", "r") as footer_file:
                footer = footer_file.read()
        except OSError as e:
            self.logger.error("can't read template files", e)
        try:
            with open(self.html_path, "w") as index_file:
                # Set date
                header = header.replace("$DATE", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                # Fill countries dropdown
                countries_options = ""
                for country in self.countries:
                    countries_options += "<option value=\"{}\">{}</option>".format(country.lower(), country.replace("_", " "))
                header = header.replace("$COUNTRIES", countries_options)
                html_output = header
                # For each mirror
                for state in self.states:
                    # Set color of row
                    if all(branch == 1 for branch in state["branches"]):
                        color = "green"
                    elif any(branch == 1 for branch in state["branches"]):
                        color = "yellow"
                    else:
                        color = "red"
                    html_output += "<tr class=\"{}\">".format(color)
                    # Pretiffy URL
                    displayed_url = state["url"].split("//")[1][:-1]
                    if len(state["url"]) > 50:
                        displayed_url = displayed_url[:47] + "..."
                    html_output += '<td><a href="{url}" data-toggle="tooltip" data-placement="top" title="{url}">{durl}</a></td>'.format(url=state["url"], durl=displayed_url)
                    # Pretiffy country
                    html_output += "<td>{}</td>".format(state["country"].replace("_", " "))
                    # Set list of protocols
                    html_output += "<td>{}</td>".format(", ".join(state["protocols"]))
                    # Set last sync
                    if state["last_sync"] == -1:
                        state["last_sync"] = "N/A"
                    html_output += "<td>{}</td>".format(state["last_sync"])
                    # Set list of states for each branch
                    icon = '<td class="{name}"><img src="../data/img/{name}.png" data-toggle="tooltip" data-placement="top" alt="{desc}" title="{desc}"></td>'
                    for i, branch in enumerate(BRANCHES):
                        if state["branches"][i] == 1:
                            html_output += icon.format(name="up", desc="Up to date")
                        elif state["branches"][i] == 0:
                            html_output += icon.format(name="out", desc="Out of date")
                        elif state["branches"][i] == -1:
                            html_output += icon.format(name="unknown", desc="Unknown")
                    html_output += "</tr>"
                html_output += footer
                index_file.write(html_output)
                self.logger.info("HTML output generated")
        except OSError as e:
            self.logger.error("can't write HTML output", e)
