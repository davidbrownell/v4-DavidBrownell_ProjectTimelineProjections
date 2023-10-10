// ----------------------------------------------------------------------
// |
// |  SharedTypes.ts
// |
// |  David Brownell <db@DavidBrownell.com>
// |      2023-09-22 09:09:16
// |
// ----------------------------------------------------------------------
// |
// |  Copyright David Brownell 2023
// |  Distributed under the Boost Software License, Version 1.0. See
// |  accompanying file LICENSE_1_0.txt or copy at
// |  http://www.boost.org/LICENSE_1_0.txt.
// |
// ----------------------------------------------------------------------


// ----------------------------------------------------------------------
// |
// |  Public Types
// |
// ----------------------------------------------------------------------
export class StatsInfo<Type> {
    constructor(
        public readonly min: Type,
        public readonly average: Type,
        public readonly max: Type,
    ) {}
};


// ----------------------------------------------------------------------
export const default_days_in_sprint = 14;
export const default_unestimated_epic_size = 25;
export const default_unestimated_feature_size = 8;
export const default_unestimated_velocity_factors: [number, number] = [0.5, 2];

export class Configuration {
    constructor(
        public any_sprint_boundary: Date,
        public days_in_sprint: number=default_days_in_sprint,
        public unestimated_epic_size: number=default_unestimated_epic_size,
        public unestimated_feature_size: number=default_unestimated_feature_size,
        public use_previous_n_sprints_for_average_velocity: number | undefined=undefined,   // Number of previous sprints to use when calculating average velocity; all previous sprints used if this value is undefined
        public unestimated_velocity_factors: [number, number]=default_unestimated_velocity_factors,  // [min, max]
        public velocity_overrides: StatsInfo<number> | undefined=undefined,
        public use_velocity_overrides_for_all_dates: boolean=false,
    ) {}

    // ----------------------------------------------------------------------
    Clone(): Configuration {
        return new Configuration(
            this.any_sprint_boundary,
            this.days_in_sprint,
            this.unestimated_epic_size,
            this.unestimated_feature_size,
            this.use_previous_n_sprints_for_average_velocity,
            this.unestimated_velocity_factors,
            this.velocity_overrides,
            this.use_velocity_overrides_for_all_dates,
        );
    }
};


// ----------------------------------------------------------------------
export class Colors {
    // Rotating colors for debug purposes

    private _colors = [
        "silver",
        "maroon",
        "purple",
        "green",
        "olive",
        "navy",
        "teal",
        "gray",
        "red",
        "fuchsia",
        "lime",
        "yellow",
        "blue",
        "aqua",
    ];

    private _index = 0;

    // ----------------------------------------------------------------------
    GetColor(): string {
        const color = this._colors[this._index];
        this._index = (this._index + 1) % this._colors.length;
        return color;
    }

    // ----------------------------------------------------------------------
    Border(
        width: number = 3,
        style: string = "solid",
    ): string {
        return `border: ${width}px ${style} ${this.GetColor()};`;
    }
};
