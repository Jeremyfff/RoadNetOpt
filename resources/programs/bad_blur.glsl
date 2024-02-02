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
uniform float directions = 16; // BLUR DIRECTIONS (Default 16.0 - More is better but slower)
uniform float quality = 3.0; // BLUR QUALITY (Default 4.0 - More is better but slower)
//https://www.shadertoy.com/view/Xltfzj
void main() {
    float Pi = 6.28318530718; // Pi*2

    vec2 radius = blurRadius / textureSize.xy;

    // Normalized pixel coordinates (from 0 to 1)
    // Pixel colour
    vec4 Color = texture(inputTexture, texcoord);
    
    // Blur calculations
    for( float d=0.0; d<Pi; d+=Pi/directions)
    {
		for(float i=1.0/quality; i<=1.0; i+=1.0/quality)
        {
			Color += texture(inputTexture, texcoord+vec2(cos(d),sin(d))*radius*i);
        }
    }
    
    // Output to screen
    Color /= quality * directions - 15.0;
    fragColor =  Color;
}
#endif
