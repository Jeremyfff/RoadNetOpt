#version 330

#if defined VERTEX_SHADER


in vec2 in_vert; // (-1 to 1)
in vec4 in_color;
uniform vec2 m_start; // (0 to 1)
uniform vec2 m_size; // (0 to 1)

out vec4 v_color;

void main() {
    vec2 offset_coord = vec2(in_vert.x * m_size.x + (m_start.x + m_size.x * 0.5) * 2.0 - 1.0 ,
                             in_vert.y * m_size.y + (m_start.y + m_size.y * 0.5) * 2.0 - 1.0);

    gl_Position = vec4(offset_coord, 0.0, 1.0);
    v_color = in_color;
}

#elif defined FRAGMENT_SHADER

in vec4 v_color;
uniform float m_alpha;
out vec4 fragColor;

void main() {
    fragColor = vec4(v_color.x, v_color.y, v_color.z, m_alpha);
}
#endif
