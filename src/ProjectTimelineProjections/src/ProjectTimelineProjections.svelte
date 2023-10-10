<!--
 ----------------------------------------------------------------------
 |
 |  ProjectTimelineProjections.svelte
 |
 |  David Brownell <db@DavidBrownell.com>
 |      2023-09-20 15:36:54
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
    "completed_color": "blue",
    "active_color": "green",
    "pending_color": "gold",

    "estimated_color": "gray",
    "unestimated_color": "lightgray",

    "min_velocity_color": "red",
    "average_velocity_color": "blue",
    "max_velocity_color": "green",

    "estimated_projection_color": "#BDB76B",
    "unestimated_projection_color": "#F0E68C",

    "velocity_width": "3px",
    "velocity_dash_size": "5px",

    "projection_average_date_color": "red",
}
]]]-->
<!--[[[end]]]-->

<!--
 ----------------------------------------------------------------------
 |
 |  Code
 |
 ----------------------------------------------------------------------
-->
<script lang=ts>
    import { onMount } from 'svelte';

    import {
        Colors,
        default_days_in_sprint,
        default_unestimated_standard_size,
        default_unestimated_large_size,
        default_unestimated_velocity_factors,
        StatsInfo,
        Configuration as ConfigurationType,
    } from './lib/impl/SharedTypes';

    import {
        CreateTimelineEvents,
        NextSprintBoundary,
        TimelineOutputEvent,
    } from './lib/impl/TimelineProjections';

    import type { TimelineInputEvent } from './lib/impl/TimelineProjections';

    import Legend from './lib/Legend.svelte';
    import Playback from './lib/Playback.svelte';
    import Settings from './lib/Settings.svelte';
    import Stats from './lib/Stats.svelte';
    import Teams from './lib/Teams.svelte';

    import Fa from 'svelte-fa';

    import {
        faChevronCircleRight,
        faCompress,
        faExpand,
        faSpinner,
        faTriangleExclamation,

    } from '@fortawesome/free-solid-svg-icons';

    import { Accordion, AccordionItem } from 'svelte-collapsible';

    // ----------------------------------------------------------------------
    // |  State Management
    // ----------------------------------------------------------------------
    export let any_sprint_boundary: Date;

    export let title: string | null = null;
    export let description: string | null = null;
    export let debug: boolean = false;

    export let url: string | null = null;
    export let titles: object | null = null;
    export let events: object | null = null;

    export let date: Date | undefined = undefined;

    export let allow_toggle_fullscreen: boolean = true;
    export let allow_playback: boolean = true;

    // [[[cog cog.outl("\n".join(f'export let {key}: string = "{value}";' for key, value in styles.items())) ]]]
    export let completed_color: string = "blue";
    export let active_color: string = "green";
    export let pending_color: string = "gold";
    export let estimated_color: string = "gray";
    export let unestimated_color: string = "lightgray";
    export let min_velocity_color: string = "red";
    export let average_velocity_color: string = "blue";
    export let max_velocity_color: string = "green";
    export let estimated_projection_color: string = "#BDB76B";
    export let unestimated_projection_color: string = "#F0E68C";
    export let velocity_width: string = "3px";
    export let velocity_dash_size: string = "5px";
    export let projection_average_date_color: string = "red";
    // [[[end]]]

    // Settings
    export let display_point_projections: boolean = true;
    export let display_velocity_extensions: boolean = true;
    export let frame_milliseconds: number = 200;

    export let debug_mode: boolean = false;

    // Calculated state
    export let height: number | string = "700px";
    export let width: number | string = "100%";

    export let is_fullscreen: boolean = false;

    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    let _error: string;
    let _date: Date | undefined = date;

    let _initialized_events: TimelineOutputEvent[];
    let _initialized_min_date: Date = new Date("2023-09-22"); // BugBug
    let _initialized_max_date: Date = new Date("2023-10-01"); // BugBug;

    let _css_var_styles: string;
    let _is_initialized: boolean = false;

    let _current_event: TimelineOutputEvent;

    const _debug_colors = new Colors();

    // Measured height and width of the element
    let _is_full_height: boolean = false;
    let _is_full_width: boolean = false;

    let _content_offset_height: number;
    let _content_offset_width: number;

    let _content_width: number;
    let _is_content_visible: boolean = true; // BugBug

    const _content_info_width = 100;

    // ----------------------------------------------------------------------
    // |  Functionality
    // ----------------------------------------------------------------------
    onMount(
        async () => {
            debug_mode = debug;

            let promise = new Promise(
                () => {
                    _css_var_styles = [
                        // [[[cog cog.outl("\n".join(f'`--{key}:${{{key}}}`,' for key in styles.keys())) ]]]
                        `--completed_color:${completed_color}`,
                        `--active_color:${active_color}`,
                        `--pending_color:${pending_color}`,
                        `--estimated_color:${estimated_color}`,
                        `--unestimated_color:${unestimated_color}`,
                        `--min_velocity_color:${min_velocity_color}`,
                        `--average_velocity_color:${average_velocity_color}`,
                        `--max_velocity_color:${max_velocity_color}`,
                        `--estimated_projection_color:${estimated_projection_color}`,
                        `--unestimated_projection_color:${unestimated_projection_color}`,
                        `--velocity_width:${velocity_width}`,
                        `--velocity_dash_size:${velocity_dash_size}`,
                        `--projection_average_date_color:${projection_average_date_color}`,
                        // [[[end]]]
                    ].join(";");
                }
            );

            if(titles !== null || events !== null) {
                if(titles === null || events === null)
                    throw Error("'titles' and 'events' must both be specified when one is specified.");
                if(url !== null)
                    throw Error("'url' must not be specified when 'titles' and 'events' are specified.")
            }
            else {
                if(url === null)
                    throw Error("'url' must be specified when 'titles' and 'events' are not specified.")

                promise = Promise.all(
                    [
                        promise,
                        fetch(
                            url,
                            {
                                cache: "no-cache",
                                method: "GET",
                            },
                        )
                            .then(
                                (response) => {
                                    if(response.status !== 200) {
                                        _error = `'${response.url}' returned '${response.statusText}' (${response.status}).`;
                                        return;
                                    }

                                    return response.json()
                                        .then(
                                            (json) => {
                                                titles = json.titles;
                                                events = json.events;
                                            }
                                        )
                                    ;
                                }
                            )
                            .catch(
                                (error) => {
                                    _error = `'${url}' returned '${error.toString()}'.`;
                                }
                            )
                    ],
                );
            }

            return promise;
        }
    );

    $: _is_initialized = titles !== null && events !== null && _css_var_styles !== null;

    $: {
        if(_is_initialized) {
            console.log(`BugBug!!!`);
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
{#if _error}
    <div class=error>
        <Fa icon={faTriangleExclamation} />{_error}
    </div>
{:else if _is_initialized}
    <div style="{_css_var_styles}">
        <h1>BugBug: {title}</h1>

        <!-- Info -->
        {#if _is_content_visible}
            <div
                class=content-info
                style={debug_mode ? _debug_colors.Border() : ""}
            >
                <Accordion key=stats duration="200ms" easing=true>
                    <AccordionItem key=stats>
                        <div slot=header>
                            <Fa icon={faChevronCircleRight} />
                            <div class=title>Stats</div>
                        </div>
                        <p slot=body>
                            <Stats
                                event={_current_event}
                                debug_mode={debug_mode}
                            />
                        </p>
                    </AccordionItem>

                    <AccordionItem key=legend>
                        <div slot=header>
                            <Fa icon={faChevronCircleRight} />
                            <div class=title>Legend</div>
                        </div>
                        <p slot=body>
                            <Legend
                                debug_mode={debug_mode}
                            />
                        </p>
                    </AccordionItem>

                    <AccordionItem key=settings>
                        <div slot=header>
                            <Fa icon={faChevronCircleRight} />
                            <div class=title>Settings</div>
                        </div>
                        <p slot=body>
                            <Settings
                                bind:display_point_projections={display_point_projections}
                                bind:display_velocity_extensions={display_velocity_extensions}
                                bind:frame_milliseconds={frame_milliseconds}
                                bind:debug_mode={debug_mode}
                            />
                        </p>
                    </AccordionItem>

                    <AccordionItem key=teams>
                        <div slot=header>
                            <Fa icon={faChevronCircleRight} />
                            <div class=title>Teams</div>
                        </div>
                        <p slot=body>
                            <Teams
                                debug_mode={debug_mode}
                            />
                        </p>
                    </AccordionItem>
                </Accordion>
            </div>
        {/if}

        <!-- Tools -->
        <div
            class=tools
            style={debug_mode ? _debug_colors.Border() : ""}
        >
            {#if allow_playback}
                <Playback
                    date={date || _initialized_min_date}
                    min_date={_initialized_min_date}
                    max_date={_initialized_max_date}
                    play_speed_milliseconds={frame_milliseconds}
                    debug_mode={debug_mode}
                    on:date_change={(event) => { _date = event.detail.date; }}
                />
            {/if}

            {#if allow_toggle_fullscreen}
                <div
                    class=fullscreen
                    style={debug_mode ? _debug_colors.Border() : ""}
                >
                    <button on:click={ () => { is_fullscreen = !is_fullscreen; }}>
                        <Fa icon={is_fullscreen ? faCompress : faExpand} />
                    </button>
                </div>
            {/if}
        </div>
    </div>
{:else}
    <Fa icon={faSpinner} spin=true />Loading content from '{url}'...
{/if}


<!--
 ----------------------------------------------------------------------
 |
 |  Style
 |
 ----------------------------------------------------------------------
-->
<style lang=sass>
    :global(.completed-size)
        fill: var(--completed_color)
        stroke: var(--completed_color)

    :global(.active-size)
        fill: var(--active_color)
        stroke: var(--active_color)

    :global(.pending-size)
        fill: var(--pending_color)
        stroke: var(--pending_color)

    :global(.estimated-size)
        fill: var(--estimated_color)
        stroke: var(--estimated_color)

    :global(.unestimated-size)
        fill: var(--unestimated_color)
        stroke: var(--unestimated_color)

    :global(.estimated-projection)
        fill: var(--estimated_projection_color)
        stroke: var(--estimated_projection_color)

    :global(.unestimated-projection)
        fill: var(--unestimated_projection_color)
        stroke: var(--unestimated_projection_color)

    :global(.min-velocity)
        fill: none
        stroke: var(--min_velocity_color)
        stroke-dasharray: var(--velocity_dash_size) var(--velocity_dash_size)
        stroke-dashoffset: 0
        stroke-width: var(--velocity_width)

    :global(.average-velocity)
        fill: none
        stroke: var(--average_velocity_color)
        stroke-dasharray: var(--velocity_dash_size) var(--velocity_dash_size)
        stroke-dashoffset: 0
        stroke-width: var(--velocity_width)

    :global(.max-velocity)
        fill: none
        stroke: var(--max_velocity_color)
        stroke-dasharray: var(--velocity_dash_size) var(--velocity_dash_size)
        stroke-dashoffset: 0
        stroke-width: var(--velocity_width)

    :global(.projection-average-date)
        fill: none
        stroke: var(--projection_average_date_color)
        stroke-dasharray: 3 3
        stroke-width: 2px
        opacity: 0.25

    :global(.sprint-boundary)
        fill: none
        stroke: black
        stroke-width: 1px
        opacity: 0.20

    :global(.svelte-fa)
        margin-right: 5px

    // BugBug .extension
    // BugBug     opacity: 0.5
    // BugBug     stroke-width: var(--velocity_width) - 2
    :global(.error)
        background-color: red
</style>
