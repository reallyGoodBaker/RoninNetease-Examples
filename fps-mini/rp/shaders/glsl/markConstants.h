#define MARK (1.0 / 255.0)
#define FPS_SCOPE_MARK 1


bool isMark(vec4 color, int mark) {
    float markColor = mark * MARK;
    return color.x == markColor && color.y == markColor && color.z == markColor && color.w == markColor;
}