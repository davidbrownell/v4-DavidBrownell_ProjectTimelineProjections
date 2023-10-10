<!--
 ----------------------------------------------------------------------
 |
 |  Legend.svelte
 |
 |  David Brownell <db@DavidBrownell.com>
 |      2023-09-22 11:21:27
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

    // ----------------------------------------------------------------------
    // |  Properties
    export let debug_mode: boolean = false;

    // ----------------------------------------------------------------------
    // |  State Management
    const _debug_colors = new Colors();

    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    const _legend_item_size_num = 20;
</script>


<!--
 ----------------------------------------------------------------------
 |
 |  Elements
 |
 ----------------------------------------------------------------------
-->
<div
    class=legend
    style={debug_mode ? _debug_colors.Border() : ""}
>
    <div class=cols>
        {#each [
            {cls: "completed-size", label: "Completed"},
            {cls: "active-size", label: "Active"},
            {cls: "pending-size", label: "Pending"},
            {cls: "estimated-size", label: "Estimated"},
            {cls: "unestimated-size", label: "Unestimated"},
            {cls: "estimated-projection", label: "Estimated Projection"},
            {cls: "unestimated-projection", label: "Unestimated Projection"},
        ] as item }
            <div class=label>{item.label}</div>
            <svg class={item.cls} width={_legend_item_size_num} height={_legend_item_size_num}>
                <rect width={_legend_item_size_num} height={_legend_item_size_num} />
            </svg>
        {/each}

        {#each [
            {cls: "projection-average-date", label: "Average Date:"},
            {cls: "average-velocity", label: "Average Velocity:"},
            {cls: "min-velocity", label: "Min Velocity:"},
            {cls: "max-velocity", label: "Max Velocity:"},
        ] as item}
            <div class=label>{item.label}</div>
            <svg class={item.cls} width={_legend_item_size_num} height={_legend_item_size_num}>
                <line x1=0 y1={_legend_item_size_num / 2} x2={_legend_item_size_num} y2={_legend_item_size_num / 2} />
            </svg>
        {/each}

        {#each [
            {cls: "sprint-boundary", label: "Sprint Boundary:"},
        ] as item }
            <div class=label>{item.label}</div>
            <svg class={item.cls} width={_legend_item_size_num} height={_legend_item_size_num}>
                <line x1={_legend_item_size_num / 2} y1=0 x2={_legend_item_size_num / 2} y2={_legend_item_size_num} />
            </svg>
        {/each}
    </div>
</div>


<!--
 ----------------------------------------------------------------------
 |
 |  Styles
 |
 ----------------------------------------------------------------------
-->
<style lang=sass>
    .legend
        @import './impl/Variables.sass'

        @include content-info-mixin

        .cols
            @include content-info-grid-mixin(116px 25px 116px 25px)

            svg rect
                opacity: 0.8

            .min-velocity
                stroke-dashoffset: 0

            .average-velocity
                stroke-dashoffset: 0

            .max-velocity
                stroke-dashoffset: 0
</style>
