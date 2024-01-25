#version 330

#if defined VERTEX_SHADER


in vec2 in_vert;
in vec4 in_color;
uniform vec2 m_offset; // (0 to 1)
uniform vec2 m_texture_size;

out vec4 v_color;

void main() {
    vec2 offset_coord = vec2(in_vert.x / m_texture_size.x + (m_offset.x * 2.0 - 1.0) ,
                             in_vert.y / m_texture_size.y + (m_offset.y * 2.0 - 1.0));

    gl_Position = vec4(offset_coord, 0.0, 1.0);
    v_color = in_color;
}

#elif defined FRAGMENT_SHADER

in vec4 v_color;

out vec4 fragColor;

void main() {
    fragColor = v_color;
}
#endif
