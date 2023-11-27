<!--
 ----------------------------------------------------------------------
 |
 |  MainGraph.svelte
 |
 |  David Brownell <db@DavidBrownell.com>
 |      2023-10-30 12:27:21
 |
 ----------------------------------------------------------------------
 |
 |  Copyright David Brownell 2023
 |  Distributed under the Boost Software License, Version 1.0. See
 |  accompanying file LICENSE_1_0.txt or copy at
 |  http://www.boost.org/LICENSE_1_0.txt.
 |
 ----------------------------------------------------------------------
-->

<!--
 ----------------------------------------------------------------------
 |
 |  Code
 |
 ----------------------------------------------------------------------
-->
<script lang=ts>
    import {
        Colors,
        StatsInfo,
    } from './impl/SharedTypes';

    import {
        CompareDates,
        IncrementDate,
        NextSprintBoundary,
        TimelineEventItem,
        ToDate,
    } from './impl/TimelineProjections';

    import * as d3 from 'd3';

    import { onMount } from 'svelte';

    // ----------------------------------------------------------------------
    export let unique_id: string;
    export let debug: boolean = false;

    export let displayed_date: Date | undefined;
    export let events: TimelineEventItem[];
    export let any_sprint_boundary: Date;
    export let days_in_sprint: number;

    export let display_counts: boolean = true;
    export let display_velocities: boolean = true;
    export let display_sizes: boolean = true;
    export let display_map: boolean = true;

    // ----------------------------------------------------------------------
    const _debug_colors = new Colors();

    const _margin_bottom = 30;
    const _margin_left = 60;
    const _margin_right = 40;
    const _margin_top = 10;

    let _init_async: any;
    let _is_initialized: boolean = false;

    let _max_display_date: Date;
    let _max_velocity: number;
    let _max_size: number;
    let _max_count: number;

    let _svg_counts: SVGElement;
    let _svg_velocities: SVGElement;
    let _svg_sizes: SVGElement;
    let _svg_map: SVGElement;

    let _displayed_events: TimelineEventItem[];
    let _displayed_event: TimelineEventItem;
    let _highlighted_event: TimelineEventItem | undefined;

    let _counts_width: number;
    let _counts_height: number;
    let _velocities_width: number;
    let _velocities_height: number;
    let _sizes_width: number;
    let _sizes_height: number;
    let _map_width: number;
    let _map_height: number;

    let _original_counts_x_scalar: any;
    let _original_counts_y_scalar: any;
    let _original_velocities_x_scalar: any;
    let _original_velocities_y_scalar: any;
    let _original_sizes_x_scalar: any;
    let _original_sizes_y_scalar: any;
    let _original_map_x_scalar: any;
    let _original_map_y_scalar: any;

    let _counts_sprint_boundaries: Date[];
    let _velocities_sprint_boundaries: Date[];
    let _sizes_sprint_boundaries: Date[];
    let _map_sprint_boundaries: Date[];

    let _counts_x_scalar: any;
    let _counts_y_scalar: any;
    let _velocities_x_scalar: any;
    let _velocities_y_scalar: any;
    let _sizes_x_scalar: any;
    let _sizes_y_scalar: any;
    let _map_x_scalar: any;
    let _map_y_scalar: any;

    // ----------------------------------------------------------------------
    onMount(
        () => {
            if(!(display_counts || display_velocities || display_sizes || display_map))
                throw new Error("One or more of 'display_counts', 'display_velocities', 'display_sizes', or 'display_map' must be true");
        }
    );

    // ----------------------------------------------------------------------
    // _max_display_date, _max_size, _max_velocity, _max_count
    $: {
        if(events) {
            const scalars_scalar = 1.1;

            let max_display_date: Date;
            let max_size: number;
            let max_velocity: number;
            let max_count: number;

            events.forEach(
                (event: TimelineEventItem) => {
                    // max_display_date
                    max_display_date = d3.max(
                        [
                            max_display_date,
                            d3.max(
                                [
                                    event.date,
                                    event.estimated?.max,
                                    event.estimated_and_unestimated?.max,
                                ],
                            ),
                        ],
                    );

                    // max_size
                    max_size = d3.max(
                        [
                            max_size,
                            event.features_estimated_size.created
                                + event.features_estimated_size.pending
                                + event.features_estimated_size.active
                                + event.features_estimated_size.completed
                                + event.epics_unestimated_size
                                + event.features_unestimated_size
                            ,
                        ],
                    );

                    // max_velocity
                    max_velocity = d3.max(
                        [
                            max_velocity,
                            event.velocity?.max,
                        ],
                    );

                    // max_count
                    max_count = d3.max(
                        [
                            max_count,
                            event.epics_estimated_num.created
                                + event.epics_estimated_num.pending
                                + event.epics_estimated_num.active
                                + event.epics_estimated_num.completed
                                + event.epics_unestimated_num.created
                                + event.epics_unestimated_num.pending
                                + event.epics_unestimated_num.active
                                + event.epics_unestimated_num.completed
                                + event.features_estimated_num.created
                                + event.features_estimated_num.pending
                                + event.features_estimated_num.active
                                + event.features_estimated_num.completed
                                + event.features_unestimated_num.created
                                + event.features_unestimated_num.pending
                                + event.features_unestimated_num.active
                                + event.features_unestimated_num.completed
                            ,
                        ],
                    );
                }
            );

            // @ts-ignore: Used before assignment
            _max_display_date = max_display_date;

            // @ts-ignore: Used before assignment
            _max_velocity = max_velocity * scalars_scalar || 1;

            // @ts-ignore: Used before assignment
            _max_size = max_size * scalars_scalar || 1;

            // @ts-ignore: Used before assignment
            _max_count = max_count * scalars_scalar || 1;
        }
    }

    // ----------------------------------------------------------------------
    // displayed_date, _displayed_events, _displayed_event
    $: {
        let displayed_date_value = displayed_date || _max_display_date;

        if(CompareDates(displayed_date_value, events[0].date) < 0)
            displayed_date_value = events[0].date;

        const displayed_events = events.filter((e: TimelineEventItem) => CompareDates(e.date, displayed_date_value) <= 0);

        _displayed_events = displayed_events;

        if(CompareDates(displayed_date_value, _displayed_events[_displayed_events.length - 1].date) > 0)
            displayed_date_value = _displayed_events[_displayed_events.length - 1].date;

        displayed_date = displayed_date_value;

        // @ts-ignore
        _displayed_event = _GetDisplayedEvent(displayed_date);
    }

    // ----------------------------------------------------------------------
    // _is_initialized
    $: {
        _is_initialized = !!(
            displayed_date
            && _displayed_events
            && _svg_counts
            && _svg_velocities
            && _svg_sizes
            && _svg_map
        );
    }

    // ----------------------------------------------------------------------
    // Graph Constants
    $: {
        if(_is_initialized) {
            // Create the Scalars
            const counts_width = d3.max([_counts_width - _margin_left - _margin_right, 0]);
            const counts_height = d3.max([_counts_height - _margin_top - _margin_bottom, 0]);

            _original_counts_x_scalar = d3.scaleTime().domain([events[0].date, events[events.length - 1].date]).range([0, counts_width]).nice();
            _original_counts_y_scalar = d3.scaleLinear().domain([0, _max_count]).range([counts_height, 0]).nice();

            const velocities_width = d3.max([_velocities_width - _margin_left - _margin_right, 0]);
            const velocities_height = d3.max([_velocities_height - _margin_top - _margin_bottom, 0]);

            _original_velocities_x_scalar = d3.scaleTime().domain([events[0].date, events[events.length - 1].date]).range([0, velocities_width]).nice();
            _original_velocities_y_scalar = d3.scaleLinear().domain([0, _max_velocity]).range([velocities_height, 0]).nice();

            const sizes_width = d3.max([_sizes_width - _margin_left - _margin_right, 0]);
            const sizes_height = d3.max([_sizes_height - _margin_top - _margin_bottom, 0]);

            _original_sizes_x_scalar = d3.scaleTime().domain([events[0].date, _max_display_date]).range([0, sizes_width]).nice();
            _original_sizes_y_scalar = d3.scaleLinear().domain([0, _max_size]).range([sizes_height, 0]).nice();

            const map_width = d3.max([_map_width - _margin_left - _margin_right, 0]);
            const map_height = d3.max([_map_height - _margin_top - _margin_bottom, 0]);

            _original_map_x_scalar = d3.scaleTime().domain([events[0].date, _max_display_date]).range([0, map_width]).nice();
            _original_map_y_scalar = d3.scaleLinear().domain([0, _max_size]).range([map_height, 0]).nice();

            // Create the sprint boundaries

            // ----------------------------------------------------------------------
            function CreateSprintBoundaries(
                domain: [Date, Date],
            ): Date[] {
                let results: Date[] = [];
                let sprint_boundary = NextSprintBoundary(
                    any_sprint_boundary,
                    days_in_sprint,
                    IncrementDate(domain[0], -days_in_sprint),
                );

                while(CompareDates(sprint_boundary, domain[1]) <= 0) {
                    results.push(sprint_boundary);
                    sprint_boundary = IncrementDate(sprint_boundary, days_in_sprint);
                }

                return results;
            }

            // ----------------------------------------------------------------------

            _counts_sprint_boundaries = CreateSprintBoundaries(_original_counts_x_scalar.domain());
            _velocities_sprint_boundaries = CreateSprintBoundaries(_original_velocities_x_scalar.domain());
            _sizes_sprint_boundaries = CreateSprintBoundaries(_original_sizes_x_scalar.domain());
            _map_sprint_boundaries = CreateSprintBoundaries(_original_map_x_scalar.domain());

            // Set the scalars to these new values
            _counts_x_scalar = _original_counts_x_scalar;
            _counts_y_scalar = _original_counts_y_scalar;
            _velocities_x_scalar = _original_velocities_x_scalar;
            _velocities_y_scalar = _original_velocities_y_scalar;
            _sizes_x_scalar = _original_sizes_x_scalar;
            _sizes_y_scalar = _original_sizes_y_scalar;
            _map_x_scalar = _original_map_x_scalar;
            _map_y_scalar = _original_map_y_scalar;
        }
    }

    // ----------------------------------------------------------------------
    // Graph Axes
    $: {
        if(_is_initialized) {
            const axis_padding = 15;

            for(
                let graph_info of [
                    {
                        cls: "counts",
                        svg: _svg_counts,
                        x_scalar: _counts_x_scalar,
                        y_scalar: _counts_y_scalar,
                        y_label: "Work Items",
                    },
                    {
                        cls: "velocities",
                        svg: _svg_velocities,
                        x_scalar: _velocities_x_scalar,
                        y_scalar: _velocities_y_scalar,
                        y_label: "Velocity",
                    },
                    {
                        cls: "sizes",
                        svg: _svg_sizes,
                        x_scalar: _sizes_x_scalar,
                        y_scalar: _sizes_y_scalar,
                        y_label: null,
                    },
                    {
                        cls: "map",
                        svg: _svg_map,
                        x_scalar: _map_x_scalar,
                        y_scalar: _map_y_scalar,
                        y_label: null,
                    },
                ]
            ) {
                const graph = d3.select(graph_info.svg);
                const width = graph_info.x_scalar.range()[1];
                const height = graph_info.y_scalar.range()[0];

                graph.select(`#clip-path-${graph_info.cls}-${unique_id} rect`)
                    .attr("width", width)
                    .attr("height", height)
                ;

                graph.select(".graph_item")
                    .attr("transform", `translate(${_margin_left}, ${_margin_top})`)
                ;

                graph.select(".xAxis")
                    .attr("transform", `translate(${_margin_left}, ${_margin_top + height})`)
                    .call(
                        d3.axisBottom(graph_info.x_scalar)
                            .tickSize(-height)
                            .tickPadding(axis_padding)
                    )
                ;

                const y_axis_callback = d3.axisLeft(graph_info.y_scalar);

                y_axis_callback
                    .tickSize(-width)
                    .tickPadding(axis_padding)
                ;

                if(!graph_info.y_label)
                    y_axis_callback.tickFormat("");

                graph.select(".yAxis")
                    .attr("transform", `translate(${_margin_left}, ${_margin_top})`)
                    .call(y_axis_callback)
                ;

                if(graph_info.y_label) {
                    graph.selectAll("text.yLabel")
                        .data([undefined])
                        .join(
                            (enter: any) => {
                                enter.append("text")
                                    .attr("class", "yLabel")
                                    .attr("transform", "rotate(-90)")
                                    .attr("y", 0)
                                    .attr("x", -height / 2)
                                    .attr("dy", "2em")
                                    .style("text-anchor", "middle")
                                    .text(graph_info.y_label)
                                ;
                            },
                            (update: any) => {
                                update.attr("x", -height / 2)
                            },
                            (exit: any) => {
                                exit
                                    .transition()
                                    .style("opacity", 0)
                                    .remove()
                                ;
                            },
                        )
                    ;
                }
            }
        }
    }

    // ----------------------------------------------------------------------
    // Graph Content
    interface CallableFillGroupFunc {
        (event: TimelineEventItem): number;
    };

    const _counts_fill_groups: Record<string, CallableFillGroupFunc> = {
        "estimated epics completed": (event: TimelineEventItem) => event.epics_estimated_num.completed,
        "unestimated epics completed": (event: TimelineEventItem) => event.epics_unestimated_num.completed,
        "estimated features completed": (event: TimelineEventItem) => event.features_estimated_num.completed,
        "unestimated features completed": (event: TimelineEventItem) => event.features_unestimated_num.completed,

        "estimated epics active": (event: TimelineEventItem) => event.epics_estimated_num.active,
        "unestimated epics active": (event: TimelineEventItem) => event.epics_unestimated_num.active,
        "estimated features active": (event: TimelineEventItem) => event.features_estimated_num.active,
        "unestimated features active": (event: TimelineEventItem) => event.features_unestimated_num.active,

        "estimated epics pending": (event: TimelineEventItem) => event.epics_estimated_num.pending,
        "unestimated epics pending": (event: TimelineEventItem) => event.epics_unestimated_num.pending,
        "estimated features pending": (event: TimelineEventItem) => event.features_estimated_num.pending,
        "unestimated features pending": (event: TimelineEventItem) => event.features_unestimated_num.pending,

        "estimated epics created": (event: TimelineEventItem) => event.epics_estimated_num.created,
        "unestimated epics created": (event: TimelineEventItem) => event.epics_unestimated_num.created,
        "estimated features created": (event: TimelineEventItem) => event.features_estimated_num.created,
        "unestimated features created": (event: TimelineEventItem) => event.features_unestimated_num.created,
    };

    const _counts_stacked_data_factory = d3.stack()
        .keys(Object.keys(_counts_fill_groups))
        .value((event: TimelineEventItem, key: string) => _counts_fill_groups[key](event))
    ;

    const _sizes_fill_groups: Record<string, CallableFillGroupFunc> = {
        "completed": (event: TimelineEventItem) => event.features_estimated_size.completed,
        "active": (event: TimelineEventItem) => event.features_estimated_size.active,
        "pending": (event: TimelineEventItem) => event.features_estimated_size.pending,
        "created": (event: TimelineEventItem) => event.features_estimated_size.created,
        "unestimated epics": (event: TimelineEventItem) => event.epics_unestimated_size,
        "unestimated features": (event: TimelineEventItem) => event.features_unestimated_size,
    };

    const _sizes_stacked_data_factory = d3.stack()
        .keys(Object.keys(_sizes_fill_groups))
        .value((event: TimelineEventItem, key: string) => _sizes_fill_groups[key](event))
    ;

    $: {
        if(_is_initialized) {
            // ----------------------------------------------------------------------
            function AddSprintBoundaries(
                cls: string,
                svg: SVGElement,
                sprint_boundaries: Date[],
                x_scalar: any,
                height: number,
            ) {
                const graph = d3.select(svg).selectAll(".graph_item");

                graph.selectAll("line.sprint-boundary")
                    .data(sprint_boundaries)
                    .join(
                        (enter: any) => {
                            enter.append("line")
                                .attr("class", "sprint-boundary")
                                .attr("clip-path", `url(#clip-path-${cls}-${unique_id}`)
                                .attr("x1", x_scalar)
                                .attr("x2", x_scalar)
                                .attr("y1", 0)
                                .attr("y2", height)
                            ;
                        },
                        (update: any) => {
                            update
                                .attr("x1", x_scalar)
                                .attr("x2", x_scalar)
                                .attr("y1", 0)
                                .attr("y2", height)
                            ;
                        },
                        (exit: any) => {
                            exit
                                .transition()
                                .style("opacity", 0)
                                .remove()
                            ;
                        },
                    )
                ;
            }

            // ----------------------------------------------------------------------

            AddSprintBoundaries("counts", _svg_counts, _counts_sprint_boundaries, _counts_x_scalar, _counts_y_scalar.range()[0]);
            AddSprintBoundaries("velocities", _svg_velocities, _velocities_sprint_boundaries, _velocities_x_scalar, _velocities_y_scalar.range()[0]);
            AddSprintBoundaries("sizes", _svg_sizes, _sizes_sprint_boundaries, _sizes_x_scalar, _sizes_y_scalar.range()[0]);
            AddSprintBoundaries("map", _svg_map, _map_sprint_boundaries, _map_x_scalar, _map_y_scalar.range()[0]);

            // Stacked items
            for(
                let graph_info of [
                    {
                        cls: "counts",
                        svg: _svg_counts,
                        x_scalar: _counts_x_scalar,
                        y_scalar: _counts_y_scalar,
                        fill_groups: _counts_fill_groups,
                        data_factory: _counts_stacked_data_factory,
                    },
                    {
                        cls: "sizes",
                        svg: _svg_sizes,
                        x_scalar: _sizes_x_scalar,
                        y_scalar: _sizes_y_scalar,
                        fill_groups: _sizes_fill_groups,
                        data_factory: _sizes_stacked_data_factory,
                    },
                    {
                        cls: "map",
                        svg: _svg_map,
                        x_scalar: _map_x_scalar,
                        y_scalar: _map_y_scalar,
                        fill_groups: _sizes_fill_groups,
                        data_factory: _sizes_stacked_data_factory,
                    },
                ]
            ) {
                const graph = d3.select(graph_info.svg).selectAll(".graph_item");

                // Stacked
                const area_calc = d3.area()
                    .x((event: any) => graph_info.x_scalar(event.data.date))
                    .y0((event: any) => graph_info.y_scalar(event[0]))
                    .y1((event: any) => graph_info.y_scalar(event[1]))
                ;

                graph.selectAll("path.stacked")
                    .data(graph_info.data_factory(_displayed_events))
                    .join(
                        (enter: any) => {
                            enter.append("path")
                                .attr("class", (event: any, key: number) => `stacked ${Object.keys(graph_info.fill_groups)[key]}`)
                                .attr("clip-path", `url(#clip-path-${graph_info.cls}-${unique_id})`)
                                .attr("d", area_calc)
                            ;
                        },
                        (update: any) => {
                            update.attr("d", area_calc);
                        },
                        (exit: any) => {
                            exit
                                .transition()
                                .style("opacity", 0)
                                .remove()
                            ;
                        },
                    )
                ;
            }

            // Velocities
            const velocities_graph = d3.select(_svg_velocities).selectAll(".graph_item");

            for(
                let graph_info of [
                    {
                        cls: "min-velocity",
                        y_value_func: (v: StatsInfo<number> | undefined) => v?.min || 0,
                    },
                    {
                        cls: "average-velocity",
                        y_value_func: (v: StatsInfo<number> | undefined) => v?.average || 0,
                    },
                    {
                        cls: "max-velocity",
                        y_value_func: (v: StatsInfo<number> | undefined) => v?.max || 0,
                    },
                ]
            ) {
                const calc = d3.line()
                    .x((event: TimelineEventItem) => _velocities_x_scalar(event.date))
                    .y((event: TimelineEventItem) => _velocities_y_scalar(graph_info.y_value_func(event.velocity)))
                ;

                velocities_graph.selectAll(`path.${graph_info.cls}`)
                    .data([undefined])
                    .join(
                        (enter: any) => {
                            enter.append("path")
                                .attr("class", graph_info.cls)
                                .attr("clip-path", `url(#clip-path-velocities-${unique_id}`)
                                .attr("d", calc(_displayed_events))
                            ;
                        },
                        (update: any) => {
                            update.attr("d", calc(_displayed_events));
                        },
                        (exit: any) => {
                            exit
                                .transition()
                                .style("opacity", 0)
                                .remove()
                            ;
                        },
                    )
                ;
            }

            _DisplayEventInfo(
                _displayed_event,
                false, // is_background
            );
        }
    }

    // ----------------------------------------------------------------------
    function _OnMouse(
        x_scalar: any,
        mouse_event: any,
    ) {
        const x: number = mouse_event.layerX - _margin_left;
        let highlighted_date: Date | undefined;

        if(mouse_event.type !== "mouseout") {
            highlighted_date = ToDate(x_scalar.invert(x));

            if(CompareDates(highlighted_date, x_scalar.domain()[0]) < 0)
                highlighted_date = undefined;
            else if(CompareDates(highlighted_date, x_scalar.domain()[1]) > 0)
                highlighted_date = undefined;
        }

        if(highlighted_date === undefined)
            _highlighted_event = undefined;
        else if(!_highlighted_event || _highlighted_event.date !== highlighted_date) {
            let highlighted_event = _GetDisplayedEvent(highlighted_date);

            if(!highlighted_event)
                highlighted_event = {
                    date: highlighted_date,
                    // @ts-ignore
                    placeholder_event: true,
                };

            _highlighted_event = highlighted_event;
        }

        // @ts-ignore
        if(highlighted_date === undefined || _highlighted_event.placeholder_event) {
            _RemoveEventInfo();
        }
        else {
            _DisplayEventInfo(
                // @ts-ignore
                _highlighted_event,
                true, // is_background
            );
        }

        // Update the display
        for(
            let graph_info of [
                {
                    cls: "counts",
                    svg: _svg_counts,
                    x_scalar: _counts_x_scalar,
                    y_scalar: _counts_y_scalar,
                },
                {
                    cls: "velocities",
                    svg: _svg_velocities,
                    x_scalar: _velocities_x_scalar,
                    y_scalar: _velocities_y_scalar,
                },
                {
                    cls: "sizes",
                    svg: _svg_sizes,
                    x_scalar: _sizes_x_scalar,
                    y_scalar: _sizes_y_scalar,
                },
                {
                    cls: "map",
                    svg: _svg_map,
                    x_scalar: _map_x_scalar,
                    y_scalar: _map_y_scalar,
                },
            ]
        ) {
            let highlight_points: any;

            if(highlighted_date === undefined)
                highlight_points = [];
            else {
                const x = graph_info.x_scalar(highlighted_date);
                const height = graph_info.y_scalar.range()[0];

                highlight_points = [
                    `M ${x} 0`,
                    `L ${x} ${height}`,
                ];
            }

            highlight_points = highlight_points.join(" ");

            const graph = d3.select(graph_info.svg).selectAll(".graph_item");

            graph.selectAll(".highlight-line")
                .data([undefined])
                .join(
                    (enter: any) => {
                        enter.insert("path", ".mouse-and-zoom")
                            .attr("class", "highlight-line")
                            .attr("clip-path", `url(#clip-path-${graph_info.cls}-${unique_id}`)
                            .attr("d", highlight_points)
                        ;
                    },
                    (update: any) => {
                        update.attr("d", highlight_points);
                    },
                    (exit: any) => {
                        exit.remove();
                    },
                )
            ;
        }
    }

    // ----------------------------------------------------------------------
    // Mouse and Zoom overlay
    $: {
        if(_is_initialized) {
            for(
                let graph_info of [
                    {
                        cls: "counts",
                        svg: _svg_counts,
                        x_scalar: _counts_x_scalar,
                        y_scalar: _counts_y_scalar,
                    },
                    {
                        cls: "velocities",
                        svg: _svg_velocities,
                        x_scalar: _velocities_x_scalar,
                        y_scalar: _velocities_y_scalar,
                    },
                    {
                        cls: "sizes",
                        svg: _svg_sizes,
                        x_scalar: _sizes_x_scalar,
                        y_scalar: _sizes_y_scalar,
                    },
                    {
                        cls: "map",
                        svg: _svg_map,
                        x_scalar: _map_x_scalar,
                        y_scalar: _map_y_scalar,
                    },
                ]
            ) {
                const graph = d3.select(graph_info.svg).selectAll(".graph_item");
                const width = graph_info.x_scalar.range()[1];
                const height = graph_info.y_scalar.range()[0];

                graph.selectAll("rect.mouse-and-zoom")
                    .data([undefined])
                    .join(
                        (enter: any) => {
                            enter.append("rect")
                                .attr("class", "mouse-and-zoom")
                                .attr("clip-path", `url(#clip-path-${graph_info.cls}-${unique_id}`)
                                .attr("width", width)
                                .attr("height", height)
                                .style("fill", "none")
                                .style("pointer-events", "all")
                                .on("mouseover mousemove mouseout", (event: any) => _OnMouse(graph_info.x_scalar, event))
                            ;
                        },
                        (update: any) => {
                            update
                                .attr("width", width)
                                .attr("height", height)
                            ;
                        },
                        (exit: any) => {
                            exit.remove();
                        },
                    )
                ;
            }
        }
    }

    // ----------------------------------------------------------------------
    function _DisplayProjection(
        this_date: Date,
        dates: StatsInfo<Date> | undefined,
        starting_size: number,
        ending_size: number,
        is_estimated: boolean,
        is_background: boolean,
    ) {
        const cls = (
            () => {
                if(is_estimated)
                    return "estimated-projection";

                return "remaining-projection";
            }
        )();

        for(
            let graph_info of [
                {
                    cls: "sizes",
                    svg: _svg_sizes,
                    x_scalar: _sizes_x_scalar,
                    y_scalar: _sizes_y_scalar,
                },
                {
                    cls: "map",
                    svg: _svg_map,
                    x_scalar: _map_x_scalar,
                    y_scalar: _map_y_scalar,
                },
            ]
        ) {
            if(is_background && graph_info.cls === "map")
                continue;

            const graph = d3.select(graph_info.svg).selectAll(".graph_item");

            let projection_commands: string[];

            if(dates !== undefined) {
                projection_commands = [
                    `M ${graph_info.x_scalar(this_date)} ${graph_info.y_scalar(ending_size)}`,
                    `L ${graph_info.x_scalar(dates.max)} ${graph_info.y_scalar(0)}`,
                    `L ${graph_info.x_scalar(dates.min)} ${graph_info.y_scalar(0)}`,
                    `L ${graph_info.x_scalar(this_date)} ${graph_info.y_scalar(starting_size)}`,
                    `L ${graph_info.x_scalar(this_date)} ${graph_info.y_scalar(ending_size)}`,
                    "Z",
                ];
            }
            else {
                const x = graph_info.x_scalar(this_date);
                const y = graph_info.y_scalar.domain()[1];

                projection_commands = [
                    `M ${x} ${y}`,
                    `L ${x} ${y}`
                ];
            }

            const projection_commands_string = projection_commands.join(" ");

            graph.selectAll(`path.projection.${cls}${is_background ? ".background" : ""}`)
                .data([undefined])
                .join(
                    (enter: any) => {
                        enter.append("path")
                            .attr("class", `projection ${cls} ${is_background ? "background" : ""}`)
                            .attr("clip-path", `url(#clip-path-${graph_info.cls}-${unique_id}`)
                            .attr("d", projection_commands_string)
                        ;
                    },
                    (update: any) => {
                        update.attr("d", projection_commands_string);
                    },
                    (exit: any) => {
                        exit
                            .transition()
                            .style("opacity", 0)
                            .remove()
                        ;
                    },
                )
            ;

            if(graph_info.cls !== "sizes")
                continue;

            // Accent lines
            for(
                let accent_info of [
                    {
                        cls: "projection-average-date",
                        start: [
                            graph_info.x_scalar(this_date),
                            (graph_info.y_scalar(starting_size) + graph_info.y_scalar(ending_size)) / 2,
                        ],
                        end: [
                            graph_info.x_scalar(dates?.average),
                            graph_info.y_scalar(0),
                        ],
                    },
                ]
            ) {
                let commands: string[];

                if(dates !== undefined) {
                    commands = [
                        `M ${accent_info.start[0]} ${accent_info.start[1]}`,
                        `L ${accent_info.end[0]} ${accent_info.end[1]}`,
                    ];
                }
                else {
                    const x = graph_info.x_scalar(this_date);
                    const y = graph_info.y_scalar.domain()[1];

                    commands = [
                        `M ${x} ${y}`,
                        `L ${x} ${y}`,
                    ];
                }

                const commands_str = commands.join(" ");

                graph.selectAll(`path.accent.${cls}.${accent_info.cls}${is_background ? ".background" : ""}`)
                    .data([undefined])
                    .join(
                        (enter: any) => {
                            enter
                                .append("path")
                                    .attr("class", `accent ${cls} ${accent_info.cls} ${is_background ? "background" : ""}`)
                                    .attr("clip-path", `url(#clip-path-${graph_info.cls}-${unique_id}`)
                                    .attr("d", commands_str)
                            ;
                        },
                        (update: any) => {
                            update.attr("d", commands_str);
                        },
                        (exit: any) => {
                            exit
                                .transition()
                                .style("opacity", 0)
                                .remove()
                            ;
                        },
                    )
                ;
            }
        }
    }

    // ----------------------------------------------------------------------
    function _DisplayEventInfo(
        event: TimelineEventItem,
        is_background: boolean,
    ) {
        _DisplayProjection(
            event.date,
            event.estimated,
            event.features_estimated_size.completed,
            event.features_estimated_size.completed + event.features_estimated_size.created + event.features_estimated_size.active + event.features_estimated_size.pending,
            true,                           // is_estimated
            is_background,
        );

        _DisplayProjection(
            event.date,
            event.estimated_and_unestimated,
            event.features_estimated_size.completed + event.features_estimated_size.created + event.features_estimated_size.active + event.features_estimated_size.pending,
            event.features_estimated_size.completed + event.features_estimated_size.created + event.features_estimated_size.active + event.features_estimated_size.pending + event.epics_unestimated_size + event.features_unestimated_size,
            false,                          // is_estimated
            is_background,
        );
    }

    // ----------------------------------------------------------------------
    function _RemoveEventInfo() {
        for(
            let graph_info of [
                {
                    svg: _svg_sizes,
                },
                {
                    svg: _svg_map,
                },
            ]
        ) {
            const graph = d3.select(graph_info.svg).selectAll(".graph_item");

            graph.selectAll(".background").remove();
        }
    }

    // ----------------------------------------------------------------------
    function _GetDisplayedEvent(
        date: Date,
    ): TimelineEventItem | undefined {
        for(let event_index in _displayed_events) {
            const event = _displayed_events[event_index];

            if(CompareDates(date, event.date) === 0)
                return event;
        }

        return undefined;
    }

    // ----------------------------------------------------------------------
    function _DisplayCountValue(
        value: number | undefined,
    ): string {
        // @ts-ignore
        if(_highlighted_event?.placeholder_event === true)
            return "-";

        if(value === undefined)
            return "0";

        return value.toString();
    }

    // ----------------------------------------------------------------------
    function _DisplayVelocityValue(
        value: number | undefined,
    ): string {
        // @ts-ignore
        if(_highlighted_event?.placeholder_event === true)
            return "-";

        if(value === undefined)
            return "0";

        return value.toFixed(2);
    }

    // ----------------------------------------------------------------------
    function _DisplaySizeValue(
        value: number | undefined,
    ): string {
        // @ts-ignore
        if(_highlighted_event?.placeholder_event === true)
            return "-";

        if(value === undefined)
            return "0";

        return value.toString();
    }

    // ----------------------------------------------------------------------
    function _DisplayDate(
        value: Date | undefined,
        force: boolean=false,
    ): string {
        // @ts-ignore
        if(!force && _highlighted_event?.placeholder_event === true)
            return "-";

        if(value === undefined)
            return "-";

        return `${value.getMonth() + 1}/${value.getDate()}/${value.getFullYear()}`;
    }
</script>

<!--
 ----------------------------------------------------------------------
 |
 |  Elements
 |
 ----------------------------------------------------------------------
-->
{#await _init_async then _data}
    <div
        class=graph
        style={debug ? _debug_colors.Border() : ""}
    >
        <div class=svg_defs>
            <svg>
                <defs>
                    <!--
                    This content should be defined in ProjectTimelineProjections.svelte, but I haven't
                    been able to get the browser to use the value when it is defined there. There is
                    probably a simple fix for this, but I just haven't been able to figure out what
                    that fix is.
                    -->
                    <pattern
                        id="pattern-stripe"
                        width="3" height="4"
                        patternUnits="userSpaceOnUse"
                        patternTransform="rotate(45)"
                    >
                        <rect width="2" height="4" transform="translate(0,0)" fill="white"></rect>
                    </pattern>
                    <mask id={`mask-stripe`}>
                        <rect x="0" y="0" width="100%" height="100%" fill={"url(#pattern-stripe)"} />
                    </mask>
                </defs>
            </svg>
        </div>

        <div
            class="counts-section section"
        >
            <div
                class=graph
                bind:clientWidth={_counts_width}
                bind:clientHeight={_counts_height}
            >
                <svg bind:this={_svg_counts}>
                    <clipPath id={`clip-path-counts-${unique_id}`}>
                        <rect />
                    </clipPath>

                    <g class=graph_item />
                    <g class=xAxis />
                    <g class=yAxis />
                </svg>
            </div>
            <div class=data>
                <table>
                    <tr>
                        <th>Type</th>
                        <th>Created</th>
                        <th>Pending</th>
                        <th>Active</th>
                        <th>Completed</th>
                        <th>Created</th>
                        <th>Pending</th>
                        <th>Active</th>
                        <th>Completed</th>
                    </tr>
                    <tr>
                        <td></td>
                        <td colspan=4>Epics</td>
                        <td colspan=4>Features</td>
                    </tr>
                    <tr>
                        <td>Estimated</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.epics_estimated_num?.created)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.epics_estimated_num?.pending)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.epics_estimated_num?.active)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.epics_estimated_num?.completed)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.features_estimated_num?.created)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.features_estimated_num?.pending)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.features_estimated_num?.active)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.features_estimated_num?.completed)}</td>
                    </tr>
                    <tr>
                        <td>Unestimated</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.epics_unestimated_num?.created)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.epics_unestimated_num?.pending)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.epics_unestimated_num?.active)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.epics_unestimated_num?.completed)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.features_unestimated_num?.created)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.features_unestimated_num?.pending)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.features_unestimated_num?.active)}</td>
                        <td>{_DisplayCountValue((_highlighted_event || _displayed_event)?.features_unestimated_num?.completed)}</td>
                    </tr>
                </table>
            </div>
        </div>

        <div class="velocities-section section">
            <div
                class=graph
                bind:clientWidth={_velocities_width}
                bind:clientHeight={_velocities_height}
            >
                <svg bind:this={_svg_velocities}>
                    <clipPath id={`clip-path-velocities-${unique_id}`}>
                        <rect />
                    </clipPath>

                    <g class=graph_item />
                    <g class=xAxis />
                    <g class=yAxis />
                </svg>
            </div>
            <div class=data>
                <table>
                    <tr>
                        <th>Min Velocity</th>
                        <th>Average Velocity</th>
                        <th>Max Velocity</th>
                    </tr>
                    <tr>
                        <td>{_DisplayVelocityValue((_highlighted_event || _displayed_event)?.velocity?.min)}</td>
                        <td>{_DisplayVelocityValue((_highlighted_event || _displayed_event)?.velocity?.average)}</td>
                        <td>{_DisplayVelocityValue((_highlighted_event || _displayed_event)?.velocity?.max)}</td>
                    </tr>
                </table>
            </div>
        </div>

        <div class="sizes-section section">
            <div
                class=graph
                bind:clientWidth={_sizes_width}
                bind:clientHeight={_sizes_height}
            >
                <svg bind:this={_svg_sizes}>
                    <clipPath id={`clip-path-sizes-${unique_id}`}>
                        <rect />
                    </clipPath>

                    <g class=graph_item />
                    <g class=xAxis />
                    <g class=yAxis />
                </svg>
            </div>
            <div class=data></div>
        </div>

        <div class="map-section section">
            <div
                class=graph
                bind:clientWidth={_map_width}
                bind:clientHeight={_map_height}
            >
                <svg bind:this={_svg_map}>
                    <clipPath id={`clip-path-map-${unique_id}`}>
                        <rect />
                    </clipPath>

                    <g class=graph_item />
                    <g class=xAxis />
                    <g class=yAxis />
                </svg>
            </div>
            <div class=data>
                <table>
                    <tr>
                        <td>Date</td>
                        <td>{_DisplayDate((_highlighted_event || _displayed_event)?.date, true)}</td>
                    </tr>
                    <tr>
                        <td>Size of Unestimated Epics</td>
                        <td>{_DisplaySizeValue((_highlighted_event || _displayed_event)?.epics_unestimated_size)}</td>
                    </tr>
                    <tr>
                        <td>Size of Unestimated Features</td>
                        <td>{_DisplaySizeValue((_highlighted_event || _displayed_event)?.features_unestimated_size)}</td>
                    </tr>
                </table>

                <table>
                    <tr>
                        <th>Type</th>
                        <th>Created</th>
                        <th>Pending</th>
                        <th>Active</th>
                        <th>Completed</th>
                    </tr>
                    <tr>
                        <td>Estimated</td>
                        <td>{_DisplaySizeValue((_highlighted_event || _displayed_event)?.features_estimated_size?.created)}</td>
                        <td>{_DisplaySizeValue((_highlighted_event || _displayed_event)?.features_estimated_size?.pending)}</td>
                        <td>{_DisplaySizeValue((_highlighted_event || _displayed_event)?.features_estimated_size?.active)}</td>
                        <td>{_DisplaySizeValue((_highlighted_event || _displayed_event)?.features_estimated_size?.completed)}</td>
                    </tr>
                    <tr>
                        <td>Unestimated</td>
                        <td>{_DisplaySizeValue((_highlighted_event || _displayed_event)?.features_unestimated_size?.created)}</td>
                        <td>{_DisplaySizeValue((_highlighted_event || _displayed_event)?.features_unestimated_size?.pending)}</td>
                        <td>{_DisplaySizeValue((_highlighted_event || _displayed_event)?.features_unestimated_size?.active)}</td>
                        <td>{_DisplaySizeValue((_highlighted_event || _displayed_event)?.features_unestimated_size?.completed)}</td>
                    </tr>
                </table>

                <table>
                    <tr>
                        <th>Type</th>
                        <th>Min</th>
                        <th>Average</th>
                        <th>Max</th>
                    </tr>
                    <tr>
                        <td>Estimated</td>
                        <td>{_DisplayDate((_highlighted_event || _displayed_event)?.estimated?.min)}</td>
                        <td>{_DisplayDate((_highlighted_event || _displayed_event)?.estimated?.average)}</td>
                        <td>{_DisplayDate((_highlighted_event || _displayed_event)?.estimated?.max)}</td>
                    </tr>
                    <tr>
                        <td>Unestimated</td>
                        <td>{_DisplayDate((_highlighted_event || _displayed_event)?.estimated_and_unestimated?.min)}</td>
                        <td>{_DisplayDate((_highlighted_event || _displayed_event)?.estimated_and_unestimated?.average)}</td>
                        <td>{_DisplayDate((_highlighted_event || _displayed_event)?.estimated_and_unestimated?.max)}</td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
{/await}

<!--
 ----------------------------------------------------------------------
 |
 |  Styles
 |
 ----------------------------------------------------------------------
-->
<style lang=sass>
    .graph
        display: flex
        flex-direction: column

        height: 100%

        font-size: 12px

        .svg_defs
            height: 0px
            flex-grow: 0

        .data
            display: flex
            justify-content: center

            th
                background-color: gray

        .counts-section
            flex-grow: 2

            .data
                table
                    width: 80%

                    td, th
                        text-align: center

                    th:first-child
                        text-align: left

                    tr:nth-child(2)
                        background-color: lightgray
                        font-weight: bold

        .velocities-section
            flex-grow: 2

            .data
                table
                    td, th
                        width: 200px
                        text-align: center

        .sizes-section
            flex-grow: 4

        .map-section
            flex-grow: 0.5

            // TODO: Do not display the map until zooming has been implemented
            .graph
                display: none

            .data
                flex-wrap: wrap

                table:nth-child(1)
                    td, th
                        width: 240px

                    td:nth-child(2)
                        text-align: center

                table:nth-child(2)
                    td, th
                        text-align: center
                        width: 100px

                    th:first-child
                        text-align: left

                    td:first-child:nth-last-child(1)
                        background-color: lightgray
                        font-weight: bold
                        text-align: center

                    td:nth-child(1)
                        text-align: left

                table:nth-child(3)
                    td, th
                        text-align: center
                        width: 125px

                    td:first-child
                        text-align: left

        .section
            display: flex
            flex-direction: column

            height: 100%

            .graph
                flex-grow: 1

            .data
                flex-grow: 0
</style>
