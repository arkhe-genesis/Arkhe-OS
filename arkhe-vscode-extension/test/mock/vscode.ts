export const workspace = {
  getConfiguration: () => ({
    get: (key: string, defaultValue: any) => defaultValue
  })
};
export default { workspace };
