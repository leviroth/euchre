export function suitToSymbol(suit) {
    switch (suit) {
    case "C":
        return "\u2663";
    case "D":
        return "\u2666";
    case "H":
        return "\u2665";
    case "S":
        return "\u2660";
    default:
        return undefined;
    }
}
