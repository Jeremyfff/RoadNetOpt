#version 330

#if defined VERTEX_SHADER

in vec2 in_vert; // (-1 to 1)
in vec4 in_color; // useless
out vec2 texcoord; // (0 to 1)

void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
    texcoord = in_vert * 0.5 + 0.5;
}

#elif defined FRAGMENT_SHADER

in vec2 texcoord;
out vec4 fragColor;

uniform sampler2D inputTexture; // input texture
uniform vec2 textureSize;  // texture size
uniform float blurRadius;  // blur radius

float gaussian(float x, float sigma) {
    return 1.0 / sqrt(2.0 * 3.14159265359 * sigma * sigma) * exp(-x * x / (2.0 * sigma * sigma));
}

void main() {
    vec2 texelSize = 1.0 / textureSize;

    vec3 result = vec3(0.0);
    float weightSum = 0.0;

    // horizontal blur
    for (int i = -5; i <= 5; ++i) {
        float offset = float(i) * blurRadius * texelSize.x;
        result += texture(inputTexture, texcoord + vec2(offset, 0.0)).rgb * gaussian(float(i), blurRadius);
        weightSum += gaussian(float(i), blurRadius);
    }

    // vertical blur
    for (int i = -5; i <= 5; ++i) {
        float offset = float(i) * blurRadius * texelSize.y;
        result += texture(inputTexture, texcoord + vec2(0.0, offset)).rgb * gaussian(float(i), blurRadius);
        weightSum += gaussian(float(i), blurRadius);
    }

    result /= weightSum;

    fragColor = vec4(result, 1.0);
}
#endif
