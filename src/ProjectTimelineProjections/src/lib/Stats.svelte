<!--
 ----------------------------------------------------------------------
 |
 |  Stats.svelte
 |
 |  David Brownell <db@DavidBrownell.com>
 |      2023-09-22 11:58:35
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
    import { Colors } from './impl/SharedTypes';
    import type { TimelineOutputEvent } from './impl/TimelineProjections';

    // ----------------------------------------------------------------------
    // |  Properties
    export let event: TimelineOutputEvent;
    export let debug_mode: boolean = false;

    // ----------------------------------------------------------------------
    // |  State Management
    const _debug_colors = new Colors();

    let _initialized = false;

    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    function _ToDateString(date: Date | undefined): string {
        if(date === undefined)
            return "";

        return `${date.getMonth() + 1} / ${date.getDate()} / ${date.getFullYear()}`;
    }

    // ----------------------------------------------------------------------
    function _GetVelocity(event: TimelineOutputEvent, attribute: string): string {
        const stats_info = event.velocity_overrides || event.average_velocities || null;

        if(stats_info === null)
            return "";

        if(stats_info[attribute] === undefined)
            return "";

        return stats_info[attribute].toString();
    }

    // ----------------------------------------------------------------------
    // Initialization
    $: _initialized = event !== undefined;
</script>


<!--
 ----------------------------------------------------------------------
 |
 |  Elements
 |
 ----------------------------------------------------------------------
-->
<div
    class=stats
    style={debug_mode ? _debug_colors.Border() : ""}
>
    {#if _initialized}
        {#each [
            {
                cls: "misc",
                label: "",
                items: [
                    {cls: "date", label: "Date:", value: _ToDateString(event.date), is_date: true},
                    {cls: "unestimated_standard", label: "Unestimated Items (Standard):", value: event.num_unestimated_standard, is_date: false},
                    {cls: "unestimated_large", label: "Unestimated Items (Large):", value: event.num_unestimated_large, is_date: false},
                ],
            },
            {
                cls: "points",
                label: "Story Points",
                items: [
                    {cls: "total", label: "Total:", value: event.total_size, is_date: false},
                    {cls: "completed", label: "Completed:", value: event.completed_size, is_date: false},
                    {cls: "active", label: "Active:", value: event.active_size, is_date: false},
                    {cls: "pending", label: "Pending:", value: event.pending_size, is_date: false},
                    {cls: "estimated", label: "Estimated:", value: event.estimated_size, is_date: false},
                    {cls: "remaining", label: "Remaining:", value: event.remaining_size, is_date: false},
                ],
            },
            {
                cls: "velocities",
                label: "Calculated Velocities",
                items: [
                    {cls: "min", label: "Min:", value: _GetVelocity(event, "min"), is_date: false},
                    {cls: "average", label: "Avg:", value: _GetVelocity(event, "average"), is_date: false},
                    {cls: "max", label: "Max:", value: _GetVelocity(event, "max"), is_date: false},
                ],
            },
            {
                cls: "estimated",
                label: "Date Projections for Estimated Points",
                items: [
                    {cls: "min", label: "Min:", value: event.estimated_dates ? _ToDateString(event.estimated_dates.min) : "", is_date: true},
                    {cls: "average", label: "Avg:", value: event.estimated_dates ? _ToDateString(event.estimated_dates.average) : "", is_date: true},
                    {cls: "max", label: "Max:", value: event.estimated_dates ? _ToDateString(event.estimated_dates.max) : "", is_date: true},
                ],
            },
            {
                cls: "unestimated",
                label: "Date Projections for Remaining Points",
                items: [
                    {cls: "min", label: "Min:", value: event.remaining_dates ? _ToDateString(event.remaining_dates.min) : "", is_date: true},
                    {cls: "average", label: "Avg:", value: event.remaining_dates ? _ToDateString(event.remaining_dates.average) : "", is_date: true},
                    {cls: "max", label: "Max:", value: event.remaining_dates ? _ToDateString(event.remaining_dates.max) : "", is_date: true},
                ],
            },
        ] as item}
            <div class={item.cls}>
                <div class=section-header>{item.label}</div>

                <div class=cols>
                    {#each item.items as item}
                        <div class="label">{item.label}</div>
                        <input disabled type=text class={`value ${item.is_date ? "date" : ""}`} value={item.value} />
                    {/each}
                </div>
            </div>
        {/each}
    {/if}
</div>

<!--
 ----------------------------------------------------------------------
 |
 |  Styles
 |
 ----------------------------------------------------------------------
-->
<style lang=sass>
    .stats
        @import './impl/Variables.sass'

        @include content-info-mixin

        .section-header
            font-weight: bold
            margin-bottom: 4px
            margin-top: 4px
            white-space: nowrap

        &>div:not(.header)
            .section-header
                grid-column: 1 / span 4

            .cols
                @include content-info-grid-mixin(66px 75px 66px 75px)

                input
                    text-align: center

                    &.date
                        font-size: $content-info-font-size - 1

                    &:not(.date)
                        font-size: $content-info-font-size
</style>
