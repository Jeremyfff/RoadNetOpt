#version 330

#if defined VERTEX_SHADER


in vec2 in_vert;
in vec4 in_color;
uniform vec2 m_xlim;
uniform vec2 m_ylim;

out vec4 v_color;

void main() {
    vec2 normalized_coord = vec2(2.0 * (in_vert.x - m_xlim.x) / (m_xlim.y - m_xlim.x) - 1.0,
                                 -2.0 * (in_vert.y - m_ylim.x) / (m_ylim.y - m_ylim.x) + 1.0);

    gl_Position = vec4(normalized_coord, 0.0, 1.0);
    v_color = in_color;
}

#elif defined FRAGMENT_SHADER

in vec4 v_color;

out vec4 fragColor;

void main() {
    fragColor = v_color;
}
#endif
