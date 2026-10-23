# Data sources

## Kentucky

The Kentucky observations come from the research project funded by the Kentucky Transportation Cabinet through Grant PON2-605-2200002513. The release contains derived summaries for the Saint Matthews deployments, rather than individual radar records, photographs or third-party maps.

The working speed convention divides native recorded speed codes by 10 to obtain km/h. Each retained passage is represented by its median signed recorded speed; window p85 is the inverse empirical 0.85 quantile of these passage medians. The convention is supported by the project's internal speed–distance–time consistency checks, rather than independent absolute calibration. Signed, zero and extreme finite summaries are retained.

A reference is a contiguous admitted export interval. Files with temporal overlap greater than 1 ms are excluded; missing intervals are not bridged. Each complete window requires at least 30 retained passages; its reference requires at least 60 and twice the window duration. All windows are contained in their references. Shared observations and unverified stability of the native field of view constrain the interpretation. Site/direction/footprint correspondence was insufficient for a cross-site allocation comparison.

## Austin

City of Austin, [Speed Management Rankings — July 2024](https://austin.widen.net/content/i0gbxqrqa8/original/Speed-Management-Rankings---2024-07.pdf?u=k4jbso&download=true). The analyzed ranking was retrieved on October 6, 2026. SHA-256 of the source PDF:

`2c379ed0702a425c643f80a72871a4304ba7cbb49d3c8a305dd7796396277653`

The 703 rows are published entries, not independently verified street segments. The published total is authoritative; any rounding difference between component sums and the total remains fixed. The public ranking does not establish later speed outcomes or the agency's historical use of a particular study attachment.

## Portland

City of Portland, [Traffic Speed](https://www.portlandmaps.com/arcgis/rest/services/Public/Transportation/MapServer/10), PortlandMaps Public/Transportation layer 10. The analyzed snapshot was retrieved on October 6, 2026. SHA-256 of the assembled source snapshot:

`5bc41267ff639ccca9ce82706955f879a01792b0ec3d644ed03bb1375a145405`

Native study records identify measurement locations, directions, collection periods and recorded p85 speeds. The analytical frame is retrospective: snapshot geography and lifetime study coverage were used to construct it. Retrieval time does not establish when records were available historically. Initial evidence ends before January 1, 2025; the primary matching and complete-direction rules yield 138 locations and 271 directions. The three comparison cohorts contain 137/269, 126/247 and 76/148 locations/directions, respectively.

These source citations identify the versions used. Municipal data remain subject to their providers' terms. This repository assigns no additional license to third-party source material.
