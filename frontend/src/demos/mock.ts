// 模拟数据 - 仅在开发环境使用
const mockData = {
  inputFolder: "D:\\gen_chm\\projects\\NS3602\\N32G435xx_V2.4.0\\docs",
  outputFolder: "D:\\code\\electron-chm\\output",
  chipConfig: {
    chipName: "N32G435xx",
    chipVersion: "2.4.0",
    Cn_WebUrl:
      "https://www.nationstech.com/product/general/n32g/n32g43x/n32g435",
    En_WebUrl: "https://nsing.com.sg/product/General/cortexm4/N32G435",
    Zip_Url: "https://www.nationstech.com/uploads/zip/175643967116967.zip",
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
