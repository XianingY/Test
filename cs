using System;
using System.IO;
using System.Windows.Forms;

namespace SimpleFileBrowser
{
    public partial class MainForm : Form
    {
        private MenuStrip menuStrip;
        private ToolStrip toolStrip;
        private TreeView treeView;
        private ListView listView;

        public MainForm()
        {
            InitializeComponent();
            InitializeFileBrowserComponents();
        }

        private void InitializeComponent()
        {
            this.Text = "简单的文件浏览器";
            this.Size = new Size(800, 600);

            // 初始化菜单
            menuStrip = new MenuStrip();


            // 初始化工具栏
            toolStrip = new ToolStrip();


            // 初始化TreeView
            treeView = new TreeView { Dock = DockStyle.Left };
            treeView.AfterSelect += TreeView_AfterSelect;

            // 初始化ListView
            listView = new ListView
            {
                Dock = DockStyle.Fill,
                View = View.List
            };
            listView.MouseDoubleClick += ListView_MouseDoubleClick;

            // 将控件添加到窗口
            Controls.Add(listView);
            Controls.Add(treeView);
            Controls.Add(toolStrip);
            Controls.Add(menuStrip);

            LoadDirectories(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile));
        }

        private void InitializeFileBrowserComponents()
        {
            // 这里可以添加初始化代码，例如填充菜单和工具栏
        }

        private void LoadDirectories(string dir)
        {
            try
            {
                DirectoryInfo di = new DirectoryInfo(dir);
                TreeNode node = new TreeNode(di.Name);
                node.Tag = di.FullName;
                node.Nodes.Add("");  // 添加一个空节点以启用展开图标
                this.treeView.Nodes.Add(node);
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }
        private void treeView_AfterSelect(object sender, TreeViewEventArgs e)
        {
            this.listView.Items.Clear();
            TreeNode node = e.Node;
            string path = (string)node.Tag;
            node.Nodes.Clear();

            try
            {
                // 加载子目录
                string[] dirs = Directory.GetDirectories(path);
                foreach (string dir in dirs)
                {
                    DirectoryInfo di = new DirectoryInfo(dir);
                    TreeNode subNode = new TreeNode(di.Name);
                    subNode.Tag = di.FullName;
                    subNode.Nodes.Add("");
                    node.Nodes.Add(subNode);
                }

                // 加载文件
                string[] files = Directory.GetFiles(path);
                foreach (string file in files)
                {
                    FileInfo fi = new FileInfo(file);
                    ListViewItem item = new ListViewItem(fi.Name);
                    item.Tag = fi.FullName;
                    this.listView.Items.Add(item);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }
        private void listView_MouseDoubleClick(object sender, MouseEventArgs e)
        {
            ListViewItem item = this.listView.GetItemAt(e.X, e.Y);
            string path = (string)item.Tag;

            if (Path.GetExtension(path) == ".txt")
            {
                System.Diagnostics.Process.Start("notepad.exe", path);
            }

        }
    }
}
