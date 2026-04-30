
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import * as d3 from 'd3';
import { geoNaturalEarth1, geoPath, _geoGraticule } from 'd3-geo';
import React, { _useRef, useEffect } from 'react';
import { _feature } from 'topojson-client';

// Mock topology for sandbox
const _mockWorld = {
  type: "Topology",
  objects: {
    countries: {
      type: "GeometryCollection",
      geometries: []
    }
  }
};

export default function ThreatMap({ threats = [], onThreatClick }: unknown) {
    const svgRef = _useRef<SVGSVGElement>(null);

    useEffect(() => {
        if (!svgRef.current) {return;}

        const svg = d3.select(svgRef.current);
        svg.selectAll('*').remove();

        const width = svgRef.current.clientWidth || 800;
        const height = 400;

        const projection = geoNaturalEarth1()
            .scale(width / 6)
            .translate([width / 2, height / 2]);

        const _path = geoPath().projection(projection);

        // Background
        svg.append('rect')
            .attr('width', width)
            .attr('height', height)
            .attr('fill', 'transparent');

        // Draw threats
        const colorScale = d3.scaleOrdinal<string>()
            .domain(['low', 'medium', 'high', 'critical'])
            .range(['#00ccff', '#ffaa00', '#ff4444', '#ff00ff']);

        svg.append('g')
            .selectAll('circle')
            .data(threats)
            .join('circle')
            .attr('cx', (d: unknown) => projection(d.coordinates || [0,0])![0])
            .attr('cy', (d: unknown) => projection(d.coordinates || [0,0])![1])
            .attr('r', (d: unknown) => (d.intensity / 5) + 2)
            .attr('fill', (d: unknown) => colorScale(d.severity))
            .attr('fill-opacity', 0.6)
            .attr('stroke', '#fff')
            .attr('stroke-width', 0.5)
            .on('click', (e, d) => onThreatClick?.(d));

    }, [threats]);

    return (
        <div className="w-full bg-black/40 border border-white/5 rounded-3xl p-6">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">🗺️ Mapa de Ameaças Global</h3>
            <svg ref={svgRef} className="w-full h-[400px]" />
        </div>
    );
}
