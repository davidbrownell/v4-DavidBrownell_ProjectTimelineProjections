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
    export let debug: boolean = false;

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
    style={debug ? _debug_colors.Border() : ""}
>
    <!-- TODO: epic decoration -->
    <!-- TODO: Average projection -->
    <div class=cols>
        {#each [
            {cls: "created", label: "Created:"},
            {cls: "pending", label: "Pending:"},
            {cls: "active", label: "Active:"},
            {cls: "completed", label: "Completed:"},
            {cls: "unestimated", label: "Unestimated:"},
            {cls: "estimated-projection", label: "Estimated Projection:"},
            {cls: "remaining-projection", label: "Remaining Projection:"},
        ] as item }
            <div class=label>{item.label}</div>
            <svg class={item.cls} width={_legend_item_size_num} height={_legend_item_size_num}>
                <rect width={_legend_item_size_num} height={_legend_item_size_num} />
            </svg>
        {/each}

        {#each [
            {cls: "projection-average-date", label: "Average Projected Date:"},
            {cls: "velocity", label: "Velocity:"},
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

        font-size: $content-info-font-size

        position: relative

        .cols
            display: grid
            grid-template-columns: 130px 25px 130px 25px 130px 25px
            grid-gap: 2px 17px
            align-items: center
</style>
