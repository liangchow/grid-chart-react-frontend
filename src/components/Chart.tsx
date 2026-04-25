import { useEffect, useRef, useMemo } from "react";
import * as d3 from "d3";
import type { Row } from "../types/Row";

type Props = {
  data: Row[];
  compressionIdx: number | null;
  recompressionIdx: number | null;
  warnings: string[];
};

const MARGIN = { top: 40, right: 30, bottom: 50, left: 60 };

function Chart({ data, compressionIdx, recompressionIdx, warnings }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const points = useMemo(
    () =>
      data
        .filter(
          (d): d is Required<Row> =>
            d.pressure != null && d.void_ratio != null && d.pressure > 0
        )
        .map((d) => ({ x: d.pressure, y: d.void_ratio })),
    [data]
  );

  useEffect(() => {
    const svg = svgRef.current;
    const container = containerRef.current;
    if (!svg || !container) return;

    // Dimensions
    const totalWidth = container.clientWidth || 600;
    const totalHeight = 400;
    const width = totalWidth - MARGIN.left - MARGIN.right;
    const height = totalHeight - MARGIN.top - MARGIN.bottom;

    // Clear previous render
    d3.select(svg).selectAll("*").remove();

    // Root group
    const root = d3
      .select(svg)
      .attr("width", totalWidth)
      .attr("height", totalHeight)
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    if (points.length === 0) {
      root
        .append("text")
        .attr("x", width / 2)
        .attr("y", height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#2d7a6b")
        .attr('stroke', '#faf8f3')
        .attr('stroke-width', 1.5)
        .transition().delay((_,i)=>200+i*80).duration(300).ease(d3.easeBackOut)
        .text("No valid data to display.");
      return;
    }

    const xExtent = d3.extent(points, (d) => d.x) as [number, number];
    const yExtent = d3.extent(points, (d) => d.y) as [number, number];

    // Pad y slightly
    const yPad = (yExtent[1] - yExtent[0]) * 0.1 || 0.05;

    // Scales
    const xScale = d3
      .scaleLog()
      .domain([xExtent[0] * 0.8, xExtent[1] * 1.2])
      .range([0, width])
      .nice();

    const yScale = d3
      .scaleLinear()
      .domain([yExtent[0] - yPad, yExtent[1] + yPad])
      .range([height, 0])
      .nice();

    // Border Rectangle  
    root
      .append('rect')
      .attr('width', width).attr('height', height)
      .attr('fill','none').attr('stroke','#d8d2c8').attr('stroke-width',1);

    // Grid lines
    const xTicks = xScale.ticks(6);
    const yTicks = yScale.ticks(6);

    root
      .append("g")
      .attr("class", "grid x-grid")
      .selectAll("line")
      .data(xTicks)
      .join("line")
      .attr("x1", (d) => xScale(d))
      .attr("x2", (d) => xScale(d))
      .attr("y1", 0)
      .attr("y2", height)
      .attr("stroke", "#e5e7eb")
      .attr("stroke-dasharray", "3,3");

    root
      .append("g")
      .attr("class", "grid y-grid")
      .selectAll("line")
      .data(yTicks)
      .join("line")
      .attr("x1", 0)
      .attr("x2", width)
      .attr("y1", (d) => yScale(d))
      .attr("y2", (d) => yScale(d))
      .attr("stroke", "#e5e7eb")
      .attr("stroke-dasharray", "3,3");

    // Axes
    const xAxis = d3
      .axisBottom(xScale)
      .ticks(6, "~g")
      .tickSize(5);

    const yAxis = d3
      .axisLeft(yScale)
      .ticks(6)
      .tickSize(5);

    root
      .append("g")
      .attr("transform", `translate(0,${height})`)
      .call(xAxis)
      .call((g) => g.select(".domain").attr("stroke", "#9ca3af"))
      .call((g) => g.selectAll(".tick line").attr("stroke", "#9ca3af"))
      .call((g) =>
        g
          .selectAll(".tick text")
          .attr("fill", "#374151")
          .attr("font-size", "11px")
      );

    root
      .append("g")
      .call(yAxis)
      .call((g) => g.select(".domain").attr("stroke", "#9ca3af"))
      .call((g) => g.selectAll(".tick line").attr("stroke", "#9ca3af"))
      .call((g) =>
        g
          .selectAll(".tick text")
          .attr("fill", "#374151")
          .attr("font-size", "11px")
      );

    // Axis labels
    root
      .append("text")
      .attr("text-anchor", "middle")
      .attr("x", width / 2)
      .attr("y", height + MARGIN.bottom - 8)
      .attr("fill", "#374151")
      .attr("font-size", "12px")
      .text("Pressure, P");

    root
      .append("text")
      .attr("text-anchor", "middle")
      .attr("transform", `rotate(-90)`)
      .attr("x", -height / 2)
      .attr("y", -MARGIN.left + 16)
      .attr("fill", "#374151")
      .attr("font-size", "12px")
      .text("Void Ratio, e");

    // Chart title
    root
      .append("text")
      .attr("text-anchor", "middle")
      .attr("x", width / 2)
      .attr("y", -MARGIN.top / 2)
      .attr("fill", "#111827")
      .attr("font-size", "14px")
      .attr("font-weight", "600")
      .text("e-log P Curve");

    // Line
    const lineGenerator = d3
      .line<{ x: number; y: number }>()
      .x((d) => xScale(d.x))
      .y((d) => yScale(d.y))
      .curve(d3.curveLinear)
      // .curve(d3.curveCatmullRom.alpha(0.5));

    root
      .append("path")
      .datum(points)
      .attr("fill", "none")
      .attr("stroke", "rgba(75, 192, 192, 0.8)")
      .attr("stroke-width", 2.5)
      .attr("d", lineGenerator);

    // Points
    const pointGroup = root.append("g").attr("class", "points");

    pointGroup
      .selectAll("circle")
      .data(points)
      .join("circle")
      .attr("cx", (d) => xScale(d.x))
      .attr("cy", (d) => yScale(d.y))
      .attr("r", 4)
      .attr("fill", "rgba(75, 192, 192, 1)")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .style("cursor", "pointer");

    // Tooltip
    const tooltip = d3
      .select(container)
      .selectAll<HTMLDivElement, null>(".d3-tooltip")
      .data([null])
      .join("div")
      .attr("class", "d3-tooltip")
      .style("position", "absolute")
      .style("pointer-events", "none")
      .style("background", "rgba(17,24,39,0.85)")
      .style("color", "#f9fafb")
      .style("border-radius", "6px")
      .style("padding", "6px 10px")
      .style("font-size", "12px")
      .style("white-space", "nowrap")
      .style("opacity", "0")
      .style("transition", "opacity 0.15s");

    pointGroup
      .selectAll<SVGCircleElement, { x: number; y: number }>("circle")
      .on("mouseover", function (event, d) {
        d3.select(this).attr("r", 6).attr("stroke", "#374151");
        tooltip
          .style("opacity", "1")
          .html(
            `Pressure: <b>${d.x.toFixed(2)}</b><br/>Void Ratio: <b>${d.y.toFixed(3)}</b>`
          );
      })
      .on("mousemove", function (event) {
        const [mx, my] = d3.pointer(event, container);
        tooltip.style("left", `${mx + 14}px`).style("top", `${my - 28}px`);
      })
      .on("mouseleave", function () {
        d3.select(this).attr("r", 4).attr("stroke", "#fff");
        tooltip.style("opacity", "0");
      });
  }, [points]);

  return (
    <div style={{ width: "100%" }}>
      {/* Stats row */}
      <div style={{ marginBottom: "8px", fontSize: "13px", color: "#374151" }}>
        {compressionIdx != null && (
          <span style={{ marginRight: "16px" }}>
            Compression Index: <strong>{compressionIdx.toFixed(3)}</strong>
          </span>
        )}
        {recompressionIdx != null && (
          <span>
            Recompression Index: <strong>{recompressionIdx.toFixed(3)}</strong>
          </span>
        )}
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div style={{ marginBottom: "8px" }}>
          {warnings.map((w, i) => (
            <div key={i} style={{ color: "#b45309", fontSize: "13px" }}>
              ⚠ {w}
            </div>
          ))}
        </div>
      )}

      {/* Chart */}
      <div ref={containerRef} style={{ position: "relative", width: "100%", height: "400px" }}>
        <svg ref={svgRef} style={{ width: "100%", height: "100%" }} />
      </div>
    </div>
  );
}

export default Chart;
