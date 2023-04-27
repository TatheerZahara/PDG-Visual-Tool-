from ast import Global
from flask import Flask, request, jsonify
from graphMod import dotToPng, openFunctionCluster, edgeFilter
from flask_cors import CORS
import base64


app = Flask(__name__)
CORS(app)

opened = set()

colors = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf"
]

unusedColors = set((
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf"))

nodeToColorMap = {}

actualDotSource = ''

@app.route('/')
def heartbeat():
    return 'I am alive'

@app.route('/submit', methods=["POST"])
def submitNewFile():
    global actualDotSource
    if request.method == 'POST':
        request_json = request.get_json()
        actualDotSource = base64.b64decode(request_json["dotSource"]).decode('utf-8')
        dotSource = dotToPng(actualDotSource)
        data = {"dotSource" : dotSource}
        return jsonify(data)
    else:
        return None


@app.route('/reset', methods=["GET"])
def resetGlobalVariables():
    global opened, actualDotSource, nodeToColorMap, unusedColors
    opened = set()
    actualDotSource = ''
    nodeToColorMap = {}
    unusedColors = set((
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf"))
    data = {"message" : 'Success'}
    return jsonify(data)

@app.route('/clickNode', methods=["POST"])
def clickNode():
    if request.method == 'POST':
        request_json = request.get_json()
        selected = request_json["selectedNode"]
        excludedEdges = request_json["excludeEdges"]
        dotSource = request_json["dotSource"]
        open_bool = True
        selectedColor = ''
        if selected in opened:
            open_bool = False
            opened.remove(selected)
            if selected in nodeToColorMap:
                unusedColors.add(nodeToColorMap[selected])
                nodeToColorMap.pop(selected)
        else:
            opened.add(selected)
            selectedColor = unusedColors.pop()
        nodeToColorMap[selected] = selectedColor
        dotSource,color,node_label = openFunctionCluster(actualDotSource,selected,open_bool, dotSource, excludedEdges, selectedColor, opened)
        if color == '':
            unusedColors.add(nodeToColorMap[selected])
            nodeToColorMap.pop(selected)
            selectedColor = ''
        data = {"dotSource" : dotSource, "selectedColor": selectedColor, "nodeLabel" : node_label}
        return jsonify(data)
    else:
        return None


@app.route('/edgeFilter', methods=["POST"])
def edgeFiltering():
    if request.method == 'POST':
        request_json = request.get_json()
        dotSource = request_json["dotSource"]
        excludedEdge = request_json["excludeEdges"]
        dotSource = edgeFilter(actualDotSource, excludedEdge, dotSource, opened, nodeToColorMap)
        data = {"dotSource" : dotSource}
        return jsonify(data)
    else:
        return None

if __name__ == '__main__':
    app.run(debug=True)

    