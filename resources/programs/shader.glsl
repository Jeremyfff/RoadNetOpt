#version 330

#if defined VERTEX_SHADER

in vec3 in_position;
in vec2 in_texcoord_0;
out vec2 texcoord;
void main() {
    gl_Position = vec4(in_position, 1.0);
    texcoord = in_texcoord_0;
}

#elif defined FRAGMENT_SHADER

in vec2 texcoord;
out vec4 fragColor;
uniform sampler2D inputTexture;

void main()
{

	fragColor = texture(inputTexture, texcoord);
}
#endif
