#define MARK (1.0 / 255.0)
#define FPS_SCOPE_MARK 1


bool isMark(vec4 color, int mark) {
    float markColor = mark * MARK;
    // alpha 才是真正起作用的 mark
    return color.a == markColor;
}