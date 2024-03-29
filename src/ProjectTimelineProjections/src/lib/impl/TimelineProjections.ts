// ----------------------------------------------------------------------
// |
// |  TimelineProjections.ts
// |
// |  David Brownell <db@DavidBrownell.com>
// |      2023-09-22 09:15:34
// |
// ----------------------------------------------------------------------
// |
// |  Copyright David Brownell 2023
// |  Distributed under the Boost Software License, Version 1.0. See
// |  accompanying file LICENSE_1_0.txt or copy at
// |  http://www.boost.org/LICENSE_1_0.txt.
// |
// ----------------------------------------------------------------------
import { Configuration, StatsInfo } from './SharedTypes';


// ----------------------------------------------------------------------
// |
// |  Public Types
// |
// ----------------------------------------------------------------------
export interface EventChange {
    readonly work_item_id: string;
    readonly epic_id: string;
    readonly size?: number;
    readonly state: string;
};


// ----------------------------------------------------------------------
export interface EventInfo {
    readonly created: number;
    readonly pending: number;
    readonly active: number;
    readonly completed: number;
};


// ----------------------------------------------------------------------
export interface Event {
    readonly date: Date;

    readonly epics_estimated_num: EventInfo;
    readonly epics_unestimated_num: EventInfo;

    readonly features_estimated_num: EventInfo;
    readonly features_unestimated_num: EventInfo;
    readonly features_estimated_size: EventInfo;

    readonly team?: string;

    readonly changes: EventChange[];
};


// ----------------------------------------------------------------------
export class TimelineEventItem {
    // ----------------------------------------------------------------------
    constructor(
        public readonly date: Date,
        public readonly is_sprint_boundary: boolean,

        public readonly estimated: StatsInfo<Date> | undefined,
        public readonly estimated_and_unestimated: StatsInfo<Date> | undefined,

        public readonly velocity: number | undefined,
        public readonly velocity_stats: StatsInfo<number> | undefined,

        public readonly epics_estimated_num: EventInfo,
        public readonly epics_unestimated_num: EventInfo,
        public readonly epics_unestimated_size: number,

        public readonly features_estimated_num: EventInfo,
        public readonly features_unestimated_num: EventInfo,
        public readonly features_estimated_size: EventInfo,
        public readonly features_unestimated_size: number,

        readonly changes: EventChange[],
    ) {}
}


// ----------------------------------------------------------------------
// |
// |  Public Functions
// |
// ----------------------------------------------------------------------
export function CompareDates(a: Date, b: Date): number {
    const ta = a.getTime();
    const tb = b.getTime();

    if(ta < tb) return -1;
    if(ta > tb) return 1;

    return 0;
}


// ----------------------------------------------------------------------
export function ToDate(date: Date | string): Date {
    var result = new Date(date);

    // Convert from UTC to local time
    result.setMinutes(result.getMinutes() + result.getTimezoneOffset());

    // Remove the time component
    result.setHours(0, 0, 0, 0);

    return result;
}


// ----------------------------------------------------------------------
export function IncrementDate(date: Date, days: number=1): Date {
    var result = new Date(date);

    result.setDate(result.getDate() + days);
    return result;
}


// ----------------------------------------------------------------------
export function NextSprintBoundary(
    any_sprint_boundary: Date,
    days_in_sprint: number,
    date: Date,
): Date {
    let result = _AlignToSprintBoundary(any_sprint_boundary, days_in_sprint, date);

    if(CompareDates(result, date) === 0)
        result = _AlignToSprintBoundary(any_sprint_boundary, days_in_sprint, IncrementDate(date));

    return result;
}


// ----------------------------------------------------------------------
export function CreateTimelineEvents(
    input_events: Event[],
    config: Configuration,
    next_sprint_start: Date,
): TimelineEventItem[] {
    input_events.sort((a, b) => CompareDates(a.date, b.date));

    next_sprint_start = ToDate(next_sprint_start);

    // ----------------------------------------------------------------------
    class VelocityCalculator {
        private _prev_completed_size: number | undefined = undefined;

        public velocities: Array<number | undefined> = [];
        public calculated_velocity_stats: StatsInfo<number> | undefined = undefined;

        // ----------------------------------------------------------------------
        public UpdateVelocity(
            completed_size: number | undefined,
        ) {
            if(completed_size !== undefined) {
                this.velocities.push(completed_size - (this._prev_completed_size || 0));
                this._prev_completed_size = completed_size;
            }
            else
                this.velocities.push(completed_size);

            const starting_index = (() => {
                if(config.use_previous_n_sprints_for_average_velocity !== undefined && this.velocities.length > config.use_previous_n_sprints_for_average_velocity)
                    return this.velocities.length - config.use_previous_n_sprints_for_average_velocity;

                return 0;
            })();

            let min_velocity = undefined;
            let max_velocity = undefined;
            let total_velocity = 0;
            let num_velocities = 0;

            for(let index = starting_index; index !== this.velocities.length; ++index) {
                const velocity = this.velocities[index];

                if(velocity === undefined || velocity === 0)
                    continue;

                total_velocity += velocity;
                num_velocities += 1;

                if(min_velocity === undefined || velocity < min_velocity)
                    min_velocity = velocity;
                if(max_velocity === undefined || velocity > max_velocity)
                    max_velocity = velocity;
            }

            min_velocity = min_velocity || 0;
            max_velocity = max_velocity || 0;

            const average_velocity = num_velocities ? total_velocity / num_velocities : 0;

            this.calculated_velocity_stats = new StatsInfo<number>(min_velocity, average_velocity, max_velocity);
        }
    };

    // ----------------------------------------------------------------------

    const velocity_calculator = new VelocityCalculator();
    const last_date = ToDate(input_events[input_events.length - 1].date);
    let prev_working_event: _WorkingEvent | undefined = undefined;

    // ----------------------------------------------------------------------
    function CreateTimelineEventItem(
        date: Date,
        input_event_start_index: number,
        input_event_end_index: number,
    ): TimelineEventItem {
        let [working_event, working_event_changes] = (() => {
            if(input_event_start_index === input_event_end_index) {
                if(prev_working_event === undefined)
                    throw new Error("Unexpected: prev_working_event_info is undefined");

                return [prev_working_event, []];
            }

            let result = new _WorkingEvent();

            for(let index = input_event_start_index; index !== input_event_end_index; ++index)
                result.Update(input_events[index]);

            return [result, result.changes];
        })();

        prev_working_event = working_event;

        const is_sprint_boundary = _AlignToSprintBoundary(
            config.any_sprint_boundary,
            config.days_in_sprint,
            date,
        ).getTime() === date.getTime();

        let current_sprint_boundary: Date;

        if(is_sprint_boundary) {
            velocity_calculator.UpdateVelocity(working_event.features_estimated_size.completed);
            current_sprint_boundary = date;
        }
        else {
            current_sprint_boundary = NextSprintBoundary(
                config.any_sprint_boundary,
                config.days_in_sprint,
                IncrementDate(date, -config.days_in_sprint),
            );
        }

        return working_event.CreateTimelineEventItem(
            date,
            is_sprint_boundary,
            current_sprint_boundary,
            config.days_in_sprint,
            config.unestimated_epic_size,
            config.unestimated_feature_size,
            config.unestimated_velocity_factors,
            velocity_calculator.velocities[velocity_calculator.velocities.length - 1],
            (() => {
                if(
                    config.velocity_overrides
                    && (config.use_velocity_overrides_for_all_dates || date === last_date)
                )
                    return config.velocity_overrides;

                return velocity_calculator.calculated_velocity_stats;
            })(),
            working_event_changes,
        );
    }

    // ----------------------------------------------------------------------

    let results: TimelineEventItem[] = [];

    let index = 0;
    let expected_date: Date | undefined = undefined;

    while(index < input_events.length) {
        const input_event = input_events[index];
        const this_date = ToDate(input_event.date);

        // @ts-ignore: isNaN
        if(!(this_date instanceof Date && !isNaN(this_date)))
            throw new Error(`Invalid date, index '${index}'.`);

        // Fill in missing dates (if necessary)
        if(expected_date !== undefined) {
            while(expected_date.getTime() !== this_date.getTime()) {
                results.push(CreateTimelineEventItem(expected_date, index, index));
                expected_date = IncrementDate(expected_date);
            }
        }

        // Group all input events associated with this day
        const starting_index = index;

        while(index !== input_events.length && ToDate(input_events[index].date).getTime() === this_date.getTime())
            index += 1;

        results.push(CreateTimelineEventItem(this_date, starting_index, index));
        expected_date = IncrementDate(this_date);
    }

    return results;

}
// ----------------------------------------------------------------------
// |
// |  Private Types
// |
// ----------------------------------------------------------------------
class _WorkingEventInfo {
    public created: number = 0;
    public pending: number = 0;
    public active: number = 0;
    public completed: number = 0;

    // ----------------------------------------------------------------------
    public Update(
        event_info: EventInfo,
    ) {
        this.created += event_info.created;
        this.pending += event_info.pending;
        this.active += event_info.active;
        this.completed += event_info.completed;
    }
}


// ----------------------------------------------------------------------
class _WorkingEvent {
    public epics_estimated_num: _WorkingEventInfo = new _WorkingEventInfo()
    public epics_unestimated_num: _WorkingEventInfo = new _WorkingEventInfo()

    public features_estimated_num: _WorkingEventInfo = new _WorkingEventInfo()
    public features_unestimated_num: _WorkingEventInfo = new _WorkingEventInfo()
    public features_estimated_size: _WorkingEventInfo = new _WorkingEventInfo()

    public changes: EventChange[] = [];

    // ----------------------------------------------------------------------
    public Update(
        event: Event,
    ) {
        this.epics_estimated_num.Update(event.epics_estimated_num);
        this.epics_unestimated_num.Update(event.epics_unestimated_num);

        this.features_estimated_num.Update(event.features_estimated_num);
        this.features_unestimated_num.Update(event.features_unestimated_num);
        this.features_estimated_size.Update(event.features_estimated_size);

        this.changes.concat(event.changes);
    }

    // ----------------------------------------------------------------------
    public CreateTimelineEventItem(
        date: Date,
        is_sprint_boundary: boolean,
        current_sprint_boundary: Date,
        days_in_sprint: number,
        unestimated_epic_size: number,
        unestimated_feature_size: number,
        unestimated_velocity_factors: [number, number], // min, max
        velocity: number | undefined,
        velocity_stats: StatsInfo<number> | undefined,
        changes: EventChange[],
    ): TimelineEventItem {
        const estimated_remaining_size = (
            this.features_estimated_size.created
            + this.features_estimated_size.pending
            + this.features_estimated_size.active
        );

        const unestimated_epics_size = (
            this.epics_unestimated_num.created
            + this.epics_unestimated_num.pending
            + this.epics_unestimated_num.active
        ) * unestimated_epic_size;

        const unestimated_features_size = (
            this.features_unestimated_num.created
            + this.features_unestimated_num.pending
            + this.features_unestimated_num.active
        ) * unestimated_feature_size;

        const unestimated_remaining_size = unestimated_epics_size + unestimated_features_size;

        let unestimated_projections = this._ProjectDates(
            current_sprint_boundary,
            days_in_sprint,
            unestimated_remaining_size * unestimated_velocity_factors[0],
            velocity_stats,
        );

        if(unestimated_projections !== undefined) {
            const max_unestimated_projections = this._ProjectDates(
                current_sprint_boundary,
                days_in_sprint,
                unestimated_remaining_size * unestimated_velocity_factors[1],
                velocity_stats,
            );

            if(max_unestimated_projections === undefined)
                throw new Error("Unexpected: max_unestimated_projections is undefined");

            // Calculate the average of the min and the max
            let average_date = new Date();

            average_date.setTime((unestimated_projections.average.getTime() + max_unestimated_projections.average.getTime()) / 2);
            average_date.setHours(0, 0, 0, 0);

            average_date = _AlignToSprintBoundary(current_sprint_boundary, days_in_sprint, average_date);

            unestimated_projections = new StatsInfo<Date>(
                unestimated_projections.min,
                average_date,
                max_unestimated_projections.max,
            );
        }

        return new TimelineEventItem(
            date,
            is_sprint_boundary,
            this._ProjectDates(
                current_sprint_boundary,
                days_in_sprint,
                estimated_remaining_size,
                velocity_stats,
            ),
            unestimated_projections,
            velocity,
            velocity_stats,
            this.epics_estimated_num,
            this.epics_unestimated_num,
            unestimated_epics_size,

            this.features_estimated_num,
            this.features_unestimated_num,
            this.features_estimated_size,
            unestimated_features_size,

            changes,
        );
    }

    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    // ----------------------------------------------------------------------
    private _ProjectDates(
        next_sprint_start: Date,
        days_in_sprint: number,
        size: number,
        velocity_stats: StatsInfo<number> | undefined,
    ): StatsInfo<Date> | undefined {
        if(velocity_stats === undefined)
            return undefined;

        if(size === 0)
            return undefined;

        if(
            velocity_stats.min === 0
            && velocity_stats.average === 0
            && velocity_stats.max === 0
        )
            return undefined;

        const min_date = this._ProjectDate(next_sprint_start, days_in_sprint, size, velocity_stats.max);
        const max_date = this._ProjectDate(next_sprint_start, days_in_sprint, size, velocity_stats.min);
        const average_date = this._ProjectDate(next_sprint_start, days_in_sprint, size, velocity_stats.average);

        return new StatsInfo<Date>(min_date, average_date, max_date);
    }

    // ----------------------------------------------------------------------
    private _ProjectDate(
        next_sprint_start: Date,
        days_in_sprint: number,
        size: number,
        velocity: number,
    ): Date {
        if(velocity === 0) {
            // This information will be used to create a chart. While is it tempting to set the
            // year to 9999, that would make for a pretty awful chart. Set it to something that
            // is a long way away, but not so far that it will cause problems.
            return new Date("2100-12-31");
        }

        const velocity_per_day = velocity / days_in_sprint;
        const remaining_days = size / velocity_per_day;
        const completion_date = IncrementDate(next_sprint_start, remaining_days);

        return _AlignToSprintBoundary(next_sprint_start, days_in_sprint, completion_date);
    }
}


// ----------------------------------------------------------------------
// |
// |  Private Functions
// |
// ----------------------------------------------------------------------
function _DaysSinceEpoch(date: Date): number {
    const milliseconds_per_day = 24 * 60 * 60 * 1000; // hours per day * minutes per hour * seconds per minute * milliseconds per second

    return Math.floor(date.getTime() / milliseconds_per_day);
}


// ----------------------------------------------------------------------
function _AlignToSprintBoundary(
    any_sprint_boundary: Date,
    days_in_sprint: number,
    date_to_align: Date,
): Date {
    const sprint_boundary_days = _DaysSinceEpoch(any_sprint_boundary);
    const align_boundary_days = _DaysSinceEpoch(date_to_align);
    const days_diff = align_boundary_days - sprint_boundary_days;
    const sprints_diff = Math.floor((days_diff + days_in_sprint - 1) / days_in_sprint);

    return IncrementDate(any_sprint_boundary, sprints_diff * days_in_sprint);
}
