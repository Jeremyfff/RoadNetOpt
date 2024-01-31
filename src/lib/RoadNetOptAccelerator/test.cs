using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ImGuiNET;
namespace RoadNetOptAccelerator
{
    public class cImGUI
    {
        public static void Run()
        {
            // 初始化Dear ImGui
            ImGui.CreateContext();
            ImGui.StyleColorsDark();

            // 渲染循环
            while (true)
            {
                // 开始一个新的ImGui窗口
                ImGui.Begin("Popup Window");

                // 在窗口中绘制文本
                ImGui.Text("This is a popup window!");

                // 结束ImGui窗口
                ImGui.End();

                // 渲染ImGui
                ImGui.Render();
            }

            // 清理Dear ImGui
            ImGui.DestroyContext();
        }
    }
}
