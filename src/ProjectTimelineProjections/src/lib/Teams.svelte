<!--
 ----------------------------------------------------------------------
 |
 |  Teams.svelte
 |
 |  David Brownell <db@DavidBrownell.com>
 |      2023-09-22 12:19:11
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
    let _initialized = false;

    // Initialization
    $: _initialized = true;
</script>


<!--
 ----------------------------------------------------------------------
 |
 |  Elements
 |
 ----------------------------------------------------------------------
-->
<div class=teams>
    {#if _initialized}
        <div
            style={debug_mode ? _debug_colors.Border() : ""}
        >
            Team-specific selection is not yet implemented
        </div>
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
    .teams
        @import './impl/Variables.sass'
        @include content-info-mixin

</style>
