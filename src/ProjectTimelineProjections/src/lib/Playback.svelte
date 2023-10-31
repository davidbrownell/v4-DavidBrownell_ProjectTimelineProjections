<!--
 ----------------------------------------------------------------------
 |
 |  Playback.svelte
 |
 |  David Brownell <db@DavidBrownell.com>
 |      2023-09-22 12:25:28
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
    import { onMount } from 'svelte';

    import { Colors } from './impl/SharedTypes';
    import { CompareDates, ToDate } from './impl/TimelineProjections';

    import { createEventDispatcher } from 'svelte';

    import Fa from 'svelte-fa'
    import {
        faBackward,
        faFastBackward,
        faFastForward,
        faPause,
        faPlay,
        faForward,

    } from '@fortawesome/free-solid-svg-icons';

    // ----------------------------------------------------------------------
    // |  Properties
    export let date: Date | undefined;
    export let min_date: Date;
    export let max_date: Date;

    export let debug: boolean = false;

    export let is_playing: boolean = false;
    export let play_speed_milliseconds: number = 200;

    // Events
    //      date_change: { date: Date }

    // ----------------------------------------------------------------------
    // |  State Management
    // ----------------------------------------------------------------------
    const _debug_colors = new Colors();

    let _play_id: number = 0;

    let _date_element: HTMLInputElement;

    let _date: Date;                        // Final calculation

    let _is_min_date: boolean;
    let _is_max_date: boolean;

    // ----------------------------------------------------------------------
    // |  Functionality
    // ----------------------------------------------------------------------
    onMount(
        async () => {
            min_date = ToDate(min_date);
            max_date = ToDate(max_date);

            _SetDate(ToDate(date || new Date()));
        }
    )

    // ----------------------------------------------------------------------
    const dispatch = createEventDispatcher();

    function _SetDate(
        date: Date | string,
    ) {
        // Update _date_buttons
        if(date instanceof String) {
            date = ToDate(date as string);
        }

        date = date as Date;

        if(CompareDates(date, min_date) < 0)
            date = min_date;
        if(CompareDates(date, max_date) > 0)
            date = max_date;

        _date = date;

        _is_min_date = CompareDates(_date, min_date) === 0;
        _is_max_date = CompareDates(_date, max_date) === 0;

        if(is_playing && _is_max_date)
            is_playing = false;

        dispatch("date_change", { date: _date });

        const zero_pad_value_func = (value: number) => {
            const result = "0" + value.toString();
            return result.substring(result.length - 2);
        };

        _date_element.value = `${date.getFullYear()}-${zero_pad_value_func(date.getMonth() + 1)}-${zero_pad_value_func(date.getDate())}`;
    }

    // ----------------------------------------------------------------------
    function _AdjustDate(delta: number) {
        var result = new Date(_date);

        result.setDate(result.getDate() + delta);

        _SetDate(ToDate(result));
    }

    // ----------------------------------------------------------------------
    function _OnStart() {
        _SetDate(min_date);
    }

    // ----------------------------------------------------------------------
    function _OnYesterday() {
        _AdjustDate(-1);
    }

    // ----------------------------------------------------------------------
    function _OnPlay() {
        if(!is_playing) {
            is_playing = true;

            const this_play_id = ++_play_id;

            setInterval(
                () => {
                    if(!is_playing || this_play_id !== _play_id)
                        return;

                    _AdjustDate(1);
                },
                play_speed_milliseconds,
            );
        }
        else
            is_playing = false;
    }

    // ----------------------------------------------------------------------
    function _OnTomorrow() {
        _AdjustDate(1);
    }

    // ----------------------------------------------------------------------
    function _OnEnd() {
        _SetDate(max_date);
    }

    // ----------------------------------------------------------------------
    function _OnDateChange(event: Event) {
        // @ts-ignore
        _SetDate(ToDate(event.target.value));
    }
</script>


<!--
 ----------------------------------------------------------------------
 |
 |  Elements
 |
 ----------------------------------------------------------------------
-->
<div class=date-navigation style={debug ? _debug_colors.Border() : ""}>
    <div class=start>
        <button disabled={is_playing || _is_min_date} on:click={_OnStart}><Fa icon={faFastBackward} /></button>
    </div>
    <div class=yesterday>
        <button disabled={is_playing || _is_min_date} on:click={_OnYesterday}><Fa icon={faBackward} /></button>
    </div>
    <div class=play>
        <button disabled={_is_max_date} on:click={_OnPlay}><Fa icon={is_playing ? faPause : faPlay} /></button>
    </div>
    <div class=tomorrow>
        <button disabled={is_playing || _is_max_date} on:click={_OnTomorrow}><Fa icon={faForward} /></button>
    </div>
    <div class=end>
        <button disabled={is_playing || _is_max_date} on:click={_OnEnd}><Fa icon={faFastForward} /></button>
    </div>
    <div class=display>
        <input
            disabled={is_playing}
            type="date"
            bind:this={_date_element}
            on:change={_OnDateChange}
        />
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
    $button-padding: 5px
    $button-margin: 3px
    $control-and-display-gap: 10px

    .date-navigation
        display: flex
        flex-direction: row
        justify-content: center
        align-content: center
        align-items: center

        button
            padding: $button-padding
            margin: $button-margin

        .display
            padding-left: $control-and-display-gap
</style>
