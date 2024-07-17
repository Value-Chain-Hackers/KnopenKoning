import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import "./Graph.css";
import {
  faSearchPlus,
  faSearchMinus,
  faSyncAlt,
  faExpand,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

const Graph: React.FC = () => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [nodes, setNodes] = useState<any[]>([]);
  const [lookupMap, setLookupMap] = useState<any>({});
  const [enabledPrefixes, setEnabledPrefixes] = useState<{
    [key: string]: boolean;
  }>({});
  const [colorMapping, setColorMapping] = useState<{ [key: string]: string }>(
    {}
  );
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [simulation, setSimulation] = useState<d3.Simulation<any, any> | null>(
    null
  );

  // Define the zoom behavior outside of useEffect so it can be used in handlers
  const zoom = d3.zoom<SVGSVGElement, unknown>().on("zoom", (event) => {
    d3.select(svgRef.current).select("g").attr("transform", event.transform as any);
  });

  useEffect(() => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      const g = svg.append("g");

      svg.call(zoom).on("dblclick.zoom", null); // Disable double-click zoom

      const newSimulation = d3
        .forceSimulation()
        .force("link", d3.forceLink().id((d: any) => d["@id"]).distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force(
          "center",
          d3.forceCenter(window.innerWidth / 2, window.innerHeight / 2)
        )
        .force("collide", d3.forceCollide().radius(50));

      setSimulation(newSimulation);
      fetchDataAndDrawGraph(g, newSimulation);
    }
  }, []);

  const fetchDataAndDrawGraph = async (
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    simulation: d3.Simulation<any, any>
  ) => {
    const response = await fetch("http://localhost:18000/graph/query");
    const data = await response.json();

    const nodesData = data["nodes"]["@graph"];
    const context = data["nodes"]["@context"];

    setNodes(nodesData);
    createColorMappingAndPrefixes(context, nodesData);
    updateGraph(g, simulation, nodesData, context);
  };

  const createColorMappingAndPrefixes = (context: any, nodesData: any[]) => {
    const prefixes = Object.entries(context);
    const newColorMapping: { [key: string]: string } = {};
    const newEnabledPrefixes: { [key: string]: boolean } = {};

    prefixes.forEach(([prefix], index) => {
      newColorMapping[prefix] = getColor(index, prefixes.length);
      newEnabledPrefixes[prefix] = true;
    });

    nodesData.forEach((node) => {
      const prefix = node["@id"].split(":")[0];
      if (!newColorMapping[prefix]) {
        const color = getColor(
          Object.keys(newColorMapping).length,
          prefixes.length + 1
        );
        newColorMapping[prefix] = color;
        newEnabledPrefixes[prefix] = true;
      }
    });

    setColorMapping(newColorMapping);
    setEnabledPrefixes(newEnabledPrefixes);
  };

  const getColor = (index: number, total: number) => {
    const hue = (index / total) * 360;
    return `hsl(${hue}, 100%, 50%)`;
  };

  const updateGraph = (
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    simulation: d3.Simulation<any, any>,
    nodesData: any[],
    context: any
  ) => {
    const filteredNodes = nodesData.filter((node) => {
      const prefix = node["@id"].split(":")[0];
      return enabledPrefixes[prefix];
    });

    const validLinks = extractLinks(filteredNodes);

    g.selectAll("*").remove();

    const link = g
      .append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(validLinks)
      .enter()
      .append("line")
      .attr("stroke-width", 2)
      .attr("stroke", "#333")
      .attr("marker-end", "url(#arrowhead)");

    const node = g
      .append("g")
      .attr("class", "nodes")
      .selectAll("circle")
      .data(filteredNodes)
      .enter()
      .append("circle")
      .attr("r", 15)
      .attr("stroke-width", 2)
      .attr("stroke", "#000")
      .attr("fill", (d: any) => {
        const prefix = d["@id"].split(":")[0];
        return colorMapping[prefix] || "#69b3a2";
      })
      .on("click", (event, d) => {
        setSelectedNode(d);
      })
      .call(
        d3
          .drag<SVGCircleElement, any>()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      );

    const label = g
      .append("g")
      .attr("class", "labels")
      .selectAll("text")
      .data(filteredNodes)
      .enter()
      .append("text")
      .attr("dy", -3)
      .attr("text-anchor", "middle")
      .attr("font-size", 10)
      .text((d) => getLabel(d["@id"]));

    simulation.nodes(filteredNodes);
    const force = simulation.force<d3.ForceLink<any, any>>("link");
    if (force) force.links(validLinks);

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);

      label.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y - 15);
    });
  };

  const extractLinks = (nodes: any[]) => {
    const links: any[] = [];

    nodes.forEach((node) => {
      if (node["rdfs:subClassOf"]) {
        links.push({
          source: node["@id"],
          target: node["rdfs:subClassOf"]["@id"],
          type: "subClassOf",
        });
      }
    });

    return links.filter(
      (link) => lookupMap[link.source] && lookupMap[link.target]
    );
  };

  const getLabel = (id: string) => {
    const node = lookupMap[id];
    if (node && node["rdfs:label"]) {
      if (Array.isArray(node["rdfs:label"])) {
        return node["rdfs:label"][0]["@value"];
      } else {
        return node["rdfs:label"]["@value"];
      }
    }
    return id;
  };

  const dragstarted = (event: any, d: any) => {
    if (!event.active) simulation?.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  };

  const dragged = (event: any, d: any) => {
    d.fx = event.x;
    d.fy = event.y;
  };

  const dragended = (event: any, d: any) => {
    if (!event.active) simulation?.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  };

  const handleZoomIn = () => {
    const svg = d3.select(svgRef.current);
    svg.transition().call(zoom.scaleBy as any, 1.2);
  };

  const handleZoomOut = () => {
    const svg = d3.select(svgRef.current);
    svg.transition().call(zoom.scaleBy as any, 0.8);
  };

  const handleFitContent = () => {
    const svg = d3.select(svgRef.current);
    svg.transition().call(zoom.transform as any, d3.zoomIdentity);
  };

  const handleRefresh = () => {
    if (svgRef.current && simulation) {
      updateGraph(
        d3.select(svgRef.current).select("g"),
        simulation,
        nodes,
        enabledPrefixes
      );
    }
  };

  return (
    <div className="graph-container">
      <ul id="prefixList">
        {Object.entries(enabledPrefixes).map(([prefix, enabled], index) => (
          <li
            key={prefix}
            style={{ backgroundColor: colorMapping[prefix] }}
            className={!enabled ? "disabled" : ""}
            onClick={() => {
              setEnabledPrefixes((prev) => ({
                ...prev,
                [prefix]: !prev[prefix],
              }));
              if (svgRef.current && simulation) {
                updateGraph(
                  d3.select(svgRef.current).select("g"),
                  simulation,
                  nodes,
                  enabledPrefixes
                );
              } else {
                console.error("svgRef.current or simulation is undefined.");
              }
            }}
          >
            {prefix}
          </li>
        ))}
      </ul>
      <div className="graph-controls">
        <button id="zoomIn" onClick={handleZoomIn}>
          <FontAwesomeIcon icon={faSearchPlus} />
        </button>
        <button id="zoomOut" onClick={handleZoomOut}>
          <FontAwesomeIcon icon={faSearchMinus} />
        </button>
        <button id="fitContent" onClick={handleFitContent}>
          <FontAwesomeIcon icon={faExpand} />
        </button>
        <button id="refreshButton" onClick={handleRefresh}>
          <FontAwesomeIcon icon={faSyncAlt} />
        </button>
      </div>
      <svg ref={svgRef} id="graph-canvas"></svg>
    </div>
  );
};

export default Graph;
