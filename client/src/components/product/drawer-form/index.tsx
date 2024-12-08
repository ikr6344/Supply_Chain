  import {
    type HttpError,
    useApiUrl,
    useCustom,
    useGetToPath,
    useGo,
    useTranslate,
  } from "@refinedev/core";
  import { DeleteButton, useAutocomplete } from "@refinedev/mui";
  import { useSearchParams } from "react-router-dom";
  import { useForm } from "@refinedev/react-hook-form";
  import { Controller } from "react-hook-form";
  import Button from "@mui/material/Button";
  import Box from "@mui/material/Box";
  import FormControl from "@mui/material/FormControl";
  import FormHelperText from "@mui/material/FormHelperText";
  import TextField from "@mui/material/TextField";
  import Paper from "@mui/material/Paper";
  import Stack from "@mui/material/Stack";
  import InputAdornment from "@mui/material/InputAdornment";
  import Autocomplete from "@mui/material/Autocomplete";
  import ToggleButton from "@mui/material/ToggleButton";
  import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
  import FormLabel from "@mui/material/FormLabel";
  import { Drawer, DrawerHeader, ProductImageUpload } from "../../../components";
  import { useImageUpload } from "../../../utils";
  import type { ICategory, IFile, IProduct, Nullable } from "../../../interfaces";

  type Props = {
    action: "create" | "edit";
  };

  export const ProductDrawerForm = (props: Props) => {
    const getToPath = useGetToPath();
    const [searchParams] = useSearchParams();
    const go = useGo();
    const t = useTranslate();
    const apiUrl = useApiUrl();

    const onDrawerCLose = () => {
      go({
        to:
          searchParams.get("to") ??
          getToPath({
            action: "list",
          }) ??
          "",
        query: {
          to: undefined,
        },
        options: {
          keepQuery: true,
        },
        type: "replace",
      });
    };

    const {
      watch,
      control,
      setValue,
      handleSubmit,
      formState: { errors },
      refineCore: { onFinish, id, formLoading },
      saveButtonProps,
    } = useForm<IProduct, HttpError, Nullable<IProduct>>({
      defaultValues: {
        name: "",
        description: "",
        rwIds:[],
        price: 0,
        manufacturerId:0,
        categoryId: null,
        isActive: true,
        image: "",
      },
      refineCoreProps: {
        redirect: false,
        onMutationSuccess: () => {
          if (props.action === "create") {
            onDrawerCLose();
          }
        },
      },
    });
    // const imageInput: IFile[] | null = watch("image");

    const { autocompleteProps } = useAutocomplete<ICategory>({
      resource: "categories",
    });
    const { autocompleteProps:user } = useAutocomplete<ICategory>({
      resource: "users",
    });
    const { autocompleteProps: rawMaterialsAutocompleteProps } =
    useAutocomplete({
      resource: "raw_materials",
    });

  const rawMaterialsOptions = rawMaterialsAutocompleteProps?.options || [];
  const { data, isLoading } = useCustom({
    url: "/users/manufacture", 
    method: "get", 
  });

  const users = data?.data || []; // Liste des utilisateurs avec le rôle "manufacture"

    

    return (
      <Drawer
        PaperProps={{ sx: { width: { sm: "100%", md: "416px" } } }}
        open
        anchor="right"
        onClose={onDrawerCLose}
      >
        <DrawerHeader
          title={t("products.actions.edit")}
          onCloseClick={onDrawerCLose}
        />
        <form
          onSubmit={handleSubmit((data) => {
            onFinish(data);
          })}
        >
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
          >
            <Controller
              control={control}
              name="image"
              defaultValue=""
              rules={{
                required: t("errors.required.field", {
                  field: "image",
                }),
              }}
              render={({ field }) => {
                return (
                  <TextField
                    {...field}
                    variant="outlined"
                    id="image"
                    label={t("image")}
                    placeholder={t("products.fields.image")}
                  />
                );
              }}
            />

            {errors.image && (
              <FormHelperText error>{errors.image.message}</FormHelperText>
            )}
          </Box>

          <Paper
            sx={{
              marginTop: "32px",
            }}
          >
            <Stack padding="24px" spacing="24px">
              <FormControl fullWidth>
                <Controller
                  control={control}
                  name="name"
                  defaultValue=""
                  rules={{
                    required: t("errors.required.field", {
                      field: "name",
                    }),
                  }}
                  render={({ field }) => {
                    return (
                      <TextField
                        {...field}
                        variant="outlined"
                        id="name"
                        label={t("products.fields.name")}
                        placeholder={t("products.fields.name")}
                      />
                    );
                  }}
                />
                {errors.name && (
                  <FormHelperText error>{errors.name.message}</FormHelperText>
                )}
              </FormControl>
              <FormControl fullWidth>
                <Controller
                  control={control}
                  name="description"
                  defaultValue=""
                  rules={{
                    required: t("errors.required.field", {
                      field: "category",
                    }),
                  }}
                  render={({ field }) => {
                    return (
                      <TextField
                        {...field}
                        variant="outlined"
                        id="description"
                        label={t("products.fields.description")}
                        placeholder={t("products.fields.description")}
                      />
                    );
                  }}
                />
                {errors.description && (
                  <FormHelperText error>
                    {errors.description.message}
                  </FormHelperText>
                )}
              </FormControl>
              <FormControl fullWidth>
    <FormLabel>{t("products.fields.rwIds")}</FormLabel>
    <Controller
      control={control}
      name="rwIds"
      defaultValue={[]}
      rules={{
        required: t("errors.required.field", {
          field: "rwIds",
        }),
      }}
      render={({ field }) => (
        <Autocomplete
          multiple
          id="rwIds"
          options={rawMaterialsOptions} // Liste des options disponibles
          getOptionLabel={(option) => option.name} // Affiche le nom dans la liste
          isOptionEqualToValue={(option, value) => option.id === value.id}
          onChange={(_, value) => {
            // Mettre à jour seulement les identifiants sélectionnés
            const ids = value.map((item) => item.id);
            field.onChange(ids);
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t("products.fields.rwIds")}
              placeholder={t("products.fields.rwIds")}
              error={!!errors.rwIds}
              helperText={errors.rwIds?.message}
            />
          )}
        />
      )}
    />
    {errors.rwIds && (
      <FormHelperText error>{errors.rwIds.message}</FormHelperText>
    )}
  </FormControl>
  {/* <FormControl fullWidth>
      <Controller
        control={control}
        name="manufacturerId"
        defaultValue={null}
        rules={{
          required: "Manufacturer is required !",
        }}
        render={({ field }) => (
          <Autocomplete
            id="manufacturerId"
            options={users}
            getOptionLabel={(option) => option.name} 
            isOptionEqualToValue={(option, value) => option.id === value.id}
            onChange={(_, value) => {
              setValue("manufacturerId", value ? value.id : null);
            }}
            loading={isLoading}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Manufacturer"
                variant="outlined"
                error={!!errors.manufacturerId}
                helperText={errors.manufacturerId?.message}
              />
            )}
          />
        )}
      />
      {errors.manufacturerId && (
        <FormHelperText error>{errors.manufacturerId.message}</FormHelperText>
      )}
    </FormControl> */}
              <FormControl fullWidth>
                <Controller
                  control={control}
                  name="price"
                  defaultValue={0}
                  rules={{
                    required: t("errors.required.field", {
                      field: "price",
                    }),
                  }}
                  render={({ field }) => {
                    return (
                      <TextField
                        {...field}
                        variant="outlined"
                        id="price"
                        label={t("products.fields.price")}
                        placeholder={t("products.fields.price")}
                        type="number"
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">$</InputAdornment>
                          ),
                        }}
                      />
                    );
                  }}
                />
                {errors.price && (
                  <FormHelperText error>{errors.price.message}</FormHelperText>
                )}
              </FormControl>
              <FormControl>
  <Controller
    control={control}
    name="categoryId"
    defaultValue={null}
    rules={{
      required: t("errors.required.field", {
        field: "category",
      }),
    }}
    render={({ field }) => (
      <Autocomplete<ICategory>
        id="category"
        {...autocompleteProps}
        onChange={(_, value) => {
          // Envoyer uniquement l'ID de la catégorie sélectionnée
          field.onChange(value ? value.id : null);
        }}
        getOptionLabel={(item) => {
          return (
            autocompleteProps?.options?.find(
              (p) => p.id?.toString() === item?.id?.toString()
            )?.title ?? ""
          );
        }}
        isOptionEqualToValue={(option, value) =>
          value === undefined ||
          option?.id?.toString() === (value?.id ?? value)?.toString()
        }
        renderInput={(params) => (
          <TextField
            {...params}
            label={t("products.fields.category.label")}
            margin="normal"
            variant="outlined"
            error={!!errors.categoryId}
            helperText={errors.categoryId?.message}
            required
          />
        )}
      />
    )}
  />
  {errors.categoryId && (
    <FormHelperText error>{errors.categoryId.message}</FormHelperText>
  )}
</FormControl>


              <FormControl>
                <FormLabel>{t("products.fields.isActive.label")}</FormLabel>
                <Controller
                  control={control}
                  name="isActive"
                  rules={{
                    validate: (value) => {
                      if (value === undefined) {
                        return t("errors.required.field", {
                          field: "isActive",
                        });
                      }
                      return true;
                    },
                  }}
                  defaultValue={false}
                  render={({ field }) => (
                    <ToggleButtonGroup
                      id="isActive"
                      {...field}
                      exclusive
                      color="primary"
                      onChange={(_, newValue) => {
                        setValue("isActive", newValue, {
                          shouldValidate: true,
                        });

                        return newValue;
                      }}
                    >
                      <ToggleButton value={true}>
                        {t("products.fields.isActive.true")}
                      </ToggleButton>
                      <ToggleButton value={false}>
                        {t("products.fields.isActive.false")}
                      </ToggleButton>
                    </ToggleButtonGroup>
                  )}
                />
                {errors.isActive && (
                  <FormHelperText error>{errors.isActive.message}</FormHelperText>
                )}
              </FormControl>
            </Stack>
          </Paper>
          <Stack
            direction="row"
            justifyContent="space-between"
            padding="16px 24px"
          >
            <Button variant="text" color="inherit" onClick={onDrawerCLose}>
              {t("buttons.cancel")}
            </Button>
            {props.action === "edit" && (
              <DeleteButton
                recordItemId={id}
                variant="contained"
                onSuccess={() => {
                  onDrawerCLose();
                }}
              />
            )}
            <Button {...saveButtonProps} variant="contained">
              {t("buttons.save")}
            </Button>
          </Stack>
        </form>
      </Drawer>
    );
  };
