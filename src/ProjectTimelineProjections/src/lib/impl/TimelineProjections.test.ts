/* TODO
import {
    IncrementDate,
    ToDate,
} from './TimelineProjections';
*/
const { IncrementDate, ToDate } = require('./TimelineProjections'); // TODO

describe('TimelineProjections', () => {

    describe('IncrementDate', () => {
        it('should increment the date by the specified number of days', () => {
            const initialDate = new Date('2023-01-01');
            const incrementedDate = IncrementDate(initialDate, 3);
            const expectedDate = new Date('2023-01-04');

            expect(incrementedDate).toEqual(expectedDate);
        });

    });

    describe('ToDate', () => {
        it('should convert a string to a Date object', () => {
            const dateStr = '2023-01-01/00:00:00';
            const convertedDate = ToDate(dateStr);
            const expectedDate = new Date(dateStr);

            expect(convertedDate).toEqual(expectedDate);
        });
    });

});
