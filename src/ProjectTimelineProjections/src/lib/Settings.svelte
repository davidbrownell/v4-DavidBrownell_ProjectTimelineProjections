<!--
 ----------------------------------------------------------------------
 |
 |  Settings.svelte
 |
 |  David Brownell <db@DavidBrownell.com>
 |      2023-09-22 11:47:17
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
    export let display_point_projections: boolean;
    export let display_velocity_extensions: boolean;
    export let frame_milliseconds: number;

    export let debug_mode: boolean = false;

    // ----------------------------------------------------------------------
    // |  State Management
    const _debug_colors = new Colors();

    let _framerate_error: boolean = false;

    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    let _initialized = false;

    $: {
        _initialized = (
            display_point_projections !== undefined
            && display_velocity_extensions !== undefined
            && frame_milliseconds !== undefined
        );
    }

    // ----------------------------------------------------------------------
    function OnFramerate(event: any) {
        const value =(() => {
            if(!event.target_value)
                return undefined;

            const value = Number(event.target.value);

            if(value <= 0)
                return undefined;

            return value;
        })();

        if(value !== undefined) {
            _framerate_error = false;
            frame_milliseconds = value;
        }
        else
            _framerate_error = true;
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
    class=settings
>
    {#if _initialized}
        <div
            class=cols
            style={debug_mode ? _debug_colors.Border() : ""}
        >
            <label class=single-line-checkbox>
                <input
                    type=checkbox
                    bind:checked={display_point_projections}
                >
                Display Point Projections
            </label>

            <label class=single-line-checkbox>
                <input
                    type=checkbox
                    bind:checked={display_velocity_extensions}
                >
                Display Velocity Extensions
            </label>

            <div>Animation Framerate (milliseconds)</div>
            <input
                type=number
                min=1
                class={_framerate_error ? "error" : ""}
                value={frame_milliseconds}
                on:input={OnFramerate}
            />

            <label class=single-line-checkbox>
                <input
                    type=checkbox
                    bind:checked={debug_mode}
                >
                Debug Mode
            </label>
        </div>
    {/if}
</div>


<!--
----------------------------------------------------------------------
|
|  Style
|
----------------------------------------------------------------------
-->
<style lang=sass>
    .settings
        @import './impl/Variables.sass'
        @include content-info-mixin

        .cols
            @include content-info-grid-mixin(200px 91px)

            .single-line-checkbox
                grid-column: 1 / span 2
</style>
