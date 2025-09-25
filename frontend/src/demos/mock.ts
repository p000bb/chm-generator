// 模拟数据 - 仅在开发环境使用
const mockData = {
  inputFolder: "D:\\gen_chm\\projects\\NS3610\\N32H76xxx_V1.1.0\\docs",
  outputFolder: "D:\\code\\electron-chm\\output",
  chipConfig: {
    chipName: "N32H76xxx",
    chipVersion: "1.1.0",
    Cn_WebUrl: "https://www.nationstech.com/product/general/n32h/n32h76x",
    En_WebUrl: "",
    Zip_Url: "https://www.nationstech.com/uploads/zip/175643944380188.zip",
  },
};

// 根据环境变量判断是否使用模拟数据
const isDev = import.meta.env.DEV;

export const mock = isDev
  ? mockData
  : {
      inputFolder: "",
      outputFolder: "",
      chipConfig: {
        chipName: "",
        chipVersion: "",
        Cn_WebUrl: "",
        En_WebUrl: "",
        Zip_Url: "",
      },
    };
