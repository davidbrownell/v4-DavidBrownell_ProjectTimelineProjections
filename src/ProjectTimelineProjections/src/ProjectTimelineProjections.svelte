<!--
 ----------------------------------------------------------------------
 |
 |  ProjectTimelineProjections.svelte
 |
 |  David Brownell <db@DavidBrownell.com>
 |      2023-10-10 15:50:09
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

<svelte:options customElement="project-timeline-projections" />

<!--[[[cog
styles: dict[str, str] = {
    "created_color": "rgba(0, 255, 255, 0.5)",
    "active_color": "green",
    "pending_color": "gold",
    "completed_color": "blue",

    "estimated_color": "gray",
    "unestimated_color": "lightgray",

    "velocity_color": "black",
    "min_velocity_color": "red",
    "average_velocity_color": "blue",
    "max_velocity_color": "green",

    "estimated_projection_color": "#BDB76B",
    "remaining_projection_color": "#F0E68C",

    "highlight_line_color": "black",

    "velocity_width": "3px",

    "projection_average_date_color": "red",
}
]]]-->
<!--[[[end]]]-->

<!-- TODOS:
- Move velocities to separate map
- Should all visuals be impacted by zoom?
- Add visual to show how projected dates have changed over time
-->


<!--
 ----------------------------------------------------------------------
 |
 |  Code
 |
 ----------------------------------------------------------------------
-->
<script lang=ts>
    import Fa from 'svelte-fa';

    import {
        faChevronCircleRight,
        faCompress,
        faExpand,
        faSpinner,
        faTriangleExclamation,

    } from '@fortawesome/free-solid-svg-icons';

    import {
        Colors,
        default_days_in_sprint,
        default_unestimated_epic_size,
        default_unestimated_feature_size,
        default_unestimated_velocity_factors,
        StatsInfo,
        Configuration,
    } from './lib/impl/SharedTypes';

    import { CollapsibleCard } from 'svelte-collapsible';

    import {
        CreateTimelineEvents,
        NextSprintBoundary,
        TimelineEventItem,
        ToDate,
    } from './lib/impl/TimelineProjections';

    import type { Event } from './lib/impl/TimelineProjections';

    import Legend from './lib/Legend.svelte';
    import Playback from './lib/Playback.svelte';
    import MainGraph from './lib/MainGraph.svelte';

    // ----------------------------------------------------------------------
    // |  State Management
    // ----------------------------------------------------------------------
    export let title: string | null = null;
    export let description: string | null = null;
    export let debug: boolean = false;

    export let url: string | null = null;
    export let titles: Record<string, string> | null = null;
    export let events: Event[] | null = null;

    export let date: Date | undefined = undefined;

    export let any_sprint_boundary: string | Date;
    export let days_in_sprint: number = default_days_in_sprint;

    export let unestimated_epic_size: number = default_unestimated_epic_size;
    export let unestimated_feature_size: number = default_unestimated_feature_size;
    export let use_previous_n_sprints_for_average_velocity: number | undefined = undefined;
    export let unestimated_velocity_factors: [number, number] = default_unestimated_velocity_factors;
    export let velocity_overrides: StatsInfo<number> | undefined = undefined;
    export let use_velocity_overrides_for_all_sprints: boolean = false;

    export let displayed_teams: Set<string> = new Set<string>();

    export let is_fullscreen: boolean = false;

    export let frame_milliseconds: number = 200;

    // [[[cog cog.outl("\n".join(f'export let {key}: string = "{value}";' for key, value in styles.items())) ]]]
    export let created_color: string = "rgba(0, 255, 255, 0.5)";
    export let active_color: string = "green";
    export let pending_color: string = "gold";
    export let completed_color: string = "blue";
    export let estimated_color: string = "gray";
    export let unestimated_color: string = "lightgray";
    export let velocity_color: string = "black";
    export let min_velocity_color: string = "red";
    export let average_velocity_color: string = "blue";
    export let max_velocity_color: string = "green";
    export let estimated_projection_color: string = "#BDB76B";
    export let remaining_projection_color: string = "#F0E68C";
    export let highlight_line_color: string = "black";
    export let velocity_width: string = "3px";
    export let projection_average_date_color: string = "red";
    // [[[end]]]

    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    const _unique_id = (Math.random() * 100000).toFixed(0);

    let _css_var_styles: string;

    const _debug_colors = new Colors();

    let _all_teams: Set<string>;

    let _current_event: TimelineEventItem | undefined;

    let _initialized_events: TimelineEventItem[];
    let _initialized_min_date: Date;
    let _initialized_max_date: Date;

    let _next_sprint_boundary: Date;

    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    let _init_promise = (
        () => {
            let init_func = async () => {
                _css_var_styles = [
                    // [[[cog cog.outl("\n".join(f'`--{key}:${{{key}}}`,' for key in styles.keys())) ]]]
                    `--created_color:${created_color}`,
                    `--active_color:${active_color}`,
                    `--pending_color:${pending_color}`,
                    `--completed_color:${completed_color}`,
                    `--estimated_color:${estimated_color}`,
                    `--unestimated_color:${unestimated_color}`,
                    `--velocity_color:${velocity_color}`,
                    `--min_velocity_color:${min_velocity_color}`,
                    `--average_velocity_color:${average_velocity_color}`,
                    `--max_velocity_color:${max_velocity_color}`,
                    `--estimated_projection_color:${estimated_projection_color}`,
                    `--remaining_projection_color:${remaining_projection_color}`,
                    `--highlight_line_color:${highlight_line_color}`,
                    `--velocity_width:${velocity_width}`,
                    `--projection_average_date_color:${projection_average_date_color}`,
                    // [[[end]]]
                ].join(";");
            };

            if(titles !== null || events !== null) {
                if(titles === null || events === null)
                    throw Error("'titles' and 'events' must both be specified when one is specified.");
                if(url !== null)
                    throw Error("'url' must not be specified when 'titles' and 'events' are specified.")
            }
            else {
                if(url === null)
                    throw Error("'url' must be specified when 'titles' and 'events' are not specified.")

                const original_init_func = init_func;

                init_func = async () => {
                    await original_init_func();

                    try {
                        const response = await fetch(
                            url!,
                            {
                                "cache": "no-cache",
                                method: "GET",
                            },
                        );

                        if(!response.ok)
                            throw new Error(`'${response.url}' returned '${response.statusText}' (${response.status}).`);

                        try {
                            const json = await response.json();

                            titles = json.titles;
                            events = json.events;
                        }
                        catch(error) {
                            throw new Error(`'${url}' returned corrupt data: '${(error as Error).toString()}'.`);
                        }
                    }
                    catch(error) {
                        throw new Error(`'${url}' returned '${(error as Error).toString()}'.`);
                    }
                };
            }

            return init_func();
        }
    )();

    // events
    $: {
        let all_teams = new Set<string>();

        events?.forEach(
            (event) => {
                // @ts-ignore
                event.date = new Date(event.date);

                if(event.team)
                    all_teams.add(event.team);
            }
        );

        _all_teams = all_teams;
    }

    // _next_sprint_boundary
    $: {
        // @ts-ignore
        if(typeof days_in_sprint === "string" || days_in_sprint instanceof String)
            // @ts-ignore
            days_in_sprint = parseInt(days_in_sprint);

        _next_sprint_boundary = NextSprintBoundary(
            ToDate(any_sprint_boundary),
            days_in_sprint,
            ToDate(new Date()),
        );
    }

    // _initialized_events
    $: {
        if(events) {
            const initialized_events = CreateTimelineEvents(
                (() => {
                    // Only display the currently selected teams
                    if(displayed_teams.size === 0)
                        return events;

                    return events.filter(
                        (event) => {
                            return event.team && displayed_teams.has(event.team);
                        },
                    );
                })(),
                new Configuration(
                    _next_sprint_boundary,
                    days_in_sprint,
                    unestimated_epic_size,
                    unestimated_feature_size,
                    use_previous_n_sprints_for_average_velocity,
                    unestimated_velocity_factors,
                    velocity_overrides,
                    use_velocity_overrides_for_all_sprints,
                ),
                _next_sprint_boundary,
            );

            if(initialized_events.length > 0) {
                _initialized_events = initialized_events;

                _initialized_min_date = initialized_events[0].date;
                _initialized_max_date = initialized_events[initialized_events.length - 1].date;
            }
        }
    }
</script>

<!--
 ----------------------------------------------------------------------
 |
 |  Elements
 |
 ----------------------------------------------------------------------
-->
<div
    class=project-timeline-projections
    style={_css_var_styles}
>
    {#await _init_promise}
        <div class=waiting>
            <Fa icon={faSpinner} spin=true />Loading content from '{url || "local data"}'...
        </div>
    {:then}
        <div
            class=header
            style={debug ? _debug_colors.Border() : ""}
        >
            <div class=title>{title}</div>
            <div class=description>{description || ""}</div>
        </div>

        <div
            class=content-info
            style={debug ? _debug_colors.Border() : ""}
        >
            <CollapsibleCard open={false} duration={0.2} easing="ease">
                <div slot=header>
                    <Fa icon={faChevronCircleRight} />
                    <div class=title>Legend</div>
                </div>
                <p slot=body>
                    <Legend
                        debug={debug}
                    />
                </p>
            </CollapsibleCard>
        </div>

        <div
            class=tools
            style={debug ? _debug_colors.Border() : ""}
        >
            <Playback
                date={date || _initialized_max_date}
                min_date={_initialized_min_date}
                max_date={_initialized_max_date}
                bind:play_speed_milliseconds={frame_milliseconds}
                debug={debug}
                on:date_change={(event) => { date = event.detail.date }}
            />

            <div
                class=fullscreen
                style={debug ? _debug_colors.Border() : ""}
            >
                <button on:click={() => { is_fullscreen = !is_fullscreen }}>
                    <Fa icon={is_fullscreen ? faCompress : faExpand} />
                </button>
            </div>
        </div>

        <div
            class=main-graph
            style={debug ? _debug_colors.Border() : ""}
        >
            <MainGraph
                unique_id={_unique_id}
                debug={debug}
                events={_initialized_events}
                any_sprint_boundary={_next_sprint_boundary}
                days_in_sprint={days_in_sprint}
                displayed_date={date}
            />
        </div>
    {:catch error}
        <div class=error>
            <Fa icon={faTriangleExclamation} />{error.message}
        </div>
    {/await}
</div>

<!--
 ----------------------------------------------------------------------
 |
 |  Styles
 |
 ----------------------------------------------------------------------
-->
<style lang=sass>
    @import './lib/impl/Variables.sass'

    $button-padding: 5px
    $button-margin: 3px

    :global(.project-timeline-projections)
        position: relative

        display: flex
        flex-direction: column

        height: 100%

        // ----------------------------------------------------------------------
        .header
            order: 0
            flex-grow: 0

            .title
                font-size: 3em
                font-weight: bold

            .description
                padding-left: 1em

        // ----------------------------------------------------------------------
        .main-graph
            order: 1
            flex-grow: 1

            padding-bottom: 20px

            :global(svg)
                height: 100%
                width: 100%

                :global(g.xAxis .tick line)
                    stroke-opacity: 0

                :global(g.yAxis .tick line)
                    stroke-opacity: 0.25
                    stroke-dasharray: 4 4

                :global(.sizes)
                    :global(path.stacked)
                        opacity: 0.85

                :global(.projection)
                    opacity: 0.5
                    stroke-width: 1px

        // ----------------------------------------------------------------------
        :global(.content-info)
            order: 2
            flex-grow: 0

            :global([aria-expanded="true"])
                :global(button)
                    :global(svg)
                        transform: rotate(90deg)

            :global(.card)
                padding-bottom: 10px

                .title
                    display: inline-block
                    font-size: 1.25em

        // ----------------------------------------------------------------------
        .tools
            flex-grow: 0

            .fullscreen
                position: absolute
                top: 0
                right: 0

                button:
                    padding: $button-padding
                    margin: $button-margin

            :global(div.date-navigation)
                position: absolute
                top: 0
                right: 0
                padding-right: calc(1em + 25px)

        // ----------------------------------------------------------------------
        :global(.pending)
            fill: var(--pending_color)

        :global(.active)
            fill: var(--active_color)

        :global(.unestimated)
            fill: var(--unestimated_color)

        :global(.epics)
            mask: url(#mask-stripe)

        :global(.created)
            fill: var(--created_color)

        :global(.completed)
            fill: var(--completed_color)

        :global(.estimated-projection)
            fill: var(--estimated_projection_color)

        :global(.remaining-projection)
            fill: var(--remaining_projection_color)

        :global(.velocity)
            stroke: var(--velocity_color)
            stroke-width: var(--velocity_width)
            fill: none

        :global(.min-velocity)
            stroke: var(--min_velocity_color)
            stroke-width: var(--velocity_width)
            fill: none

        :global(.average-velocity)
            stroke: var(--average_velocity_color)
            stroke-width: var(--velocity_width)
            fill: none

        :global(.max-velocity)
            stroke: var(--max_velocity_color)
            stroke-width: var(--velocity_width)
            fill: none

        :global(.sprint-boundary)
            stroke: gray
            opacity: 0.5

        :global(.projection-average-date)
            stroke: var(--projection_average_date_color)

        :global(.highlight-line)
            stroke: var(--highlight_line_color)
            stroke-width: 2px

        :global(.counts)
            :global(path.stacked)
                opacity: 1
</style>
