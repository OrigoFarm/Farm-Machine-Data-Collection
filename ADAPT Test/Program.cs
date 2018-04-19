using System.Collections.Generic;
using AgGateway.ADAPT.ApplicationDataModel.ADM;
using AgGateway.ADAPT.PluginManager;

namespace JD
{
    class Program
    {
        static void Main(string[] args)
        {
            //Full path of the plugin directory. The license file needs to be placed in the same directory
            var PLUGIN_PATH = "C:\\Users\\home\\source\\repos\\JD\\plugins";
            //Full path of the datacard that contains the dataset exported from display
            var DATACARD_PATH = "C:\\Users\\home\\Desktop\\DataCard";
            //Application ID that was obtained from signing up as a John Deere developer licensee
            var GUID = "{00000000-0000-0000-0000-000000000000}";

            PluginFactory factory = new PluginFactory(PLUGIN_PATH);
            var names = factory.AvailablePlugins;
            foreach (string pluginName in names)
            {
                IPlugin plugin = factory.GetPlugin(pluginName);
                plugin.Initialize(GUID);
                if (plugin.IsDataCardSupported(DATACARD_PATH))
                {
                    IList<ApplicationDataModel> dataModel = plugin.Import(DATACARD_PATH);

                    //Test some output from datamodel
                    var crops = dataModel[0].Catalog.Crops;
                    foreach (var crop in crops)
                    {
                        System.Diagnostics.Debug.WriteLine(crop.Name);
                    }
                }
            }
        }
    }
}