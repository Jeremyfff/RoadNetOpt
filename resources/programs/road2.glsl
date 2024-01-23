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

#elif defined GEOMETRY_SHADER
layout (lines) in;
layout(triangle_strip, max_vertices = 4) out;

uniform vec2  m_viewportSize;
uniform float m_thickness = 4;

in gl_PerVertex
{
  vec4 gl_Position;
} gl_in[];

void main() {


 //https://stackoverflow.com/questions/54686818/glsl-geometry-shader-to-replace-gllinewidth
    vec4 p1 = gl_in[0].gl_Position;
    vec4 p2 = gl_in[1].gl_Position;

    vec2 dir  = normalize((p2.xy/p2.w - p1.xy/p1.w) * m_viewportSize);
    vec2 offset = vec2(-dir.y, dir.x) * m_thickness / m_viewportSize;

    gl_Position = p1 + vec4(offset.xy * p1.w, 0.0, 0.0);
    EmitVertex();
    gl_Position = p1 - vec4(offset.xy * p1.w, 0.0, 0.0);
    EmitVertex();
    gl_Position = p2 + vec4(offset.xy * p2.w, 0.0, 0.0);
    EmitVertex();
    gl_Position = p2 - vec4(offset.xy * p2.w, 0.0, 0.0);
    EmitVertex();

    EndPrimitive();
}

#elif defined FRAGMENT_SHADER

in vec4 v_color;

out vec4 fragColor;

void main() {
    fragColor = v_color;
}
#endif
